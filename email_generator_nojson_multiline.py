import requests
import json
import os
import time
import re

# =========================
# CONFIGURATION
# =========================
MODEL_NAME = "llama3.2:3b-instruct-q4_0"
OLLAMA_URL = "http://localhost:11434/api/generate"
OUTPUT_DIR = "emails"
DEBUG_DIR = "emails/debug"  # Separate debug folder
NUM_EMAILS = 20
DELAY_SECONDS = 0.3
MAX_RETRIES = 3

# =========================
# PROMPTS
# =========================
SYSTEM_PROMPT = """You are an email generator. You MUST output ONLY the four fields: SUBJECT, BODY, TONE, INTENT. Do not add explanations, preambles, or markdown. Follow the exact format specified."""

USER_PROMPT = """Generate a professional recruiting coordinator email inviting a candidate to an interview.

REQUIREMENTS:
- Invent realistic fictional names (candidate, company, interviewer, role, sender)
- Include interview date, time, and format
- Professional, friendly, respectful tone
- No double quotes anywhere
- Address candidate by first name
- Provide complete interview details
- Ask for confirmation or alternatives
- Professional closing and signature

CRITICAL:
- You MUST output ONLY the four fields shown below
- Use the EXACT same format and field order as the example
- Do NOT add any text before SUBJECT or after INTENT

EXAMPLE OUTPUT (FORMAT MUST MATCH EXACTLY):

SUBJECT: Interview Invitation for Data Analyst Role at BrightWave Solutions

BODY:
Hi Jordan,

Thank you for your interest in the Data Analyst position at BrightWave Solutions. We were impressed with your background and would like to invite you to participate in an interview.

The interview is scheduled for Tuesday, April 9 at 10:30 AM PST and will be conducted via Zoom. You will be meeting with Alex Martinez, Senior Analytics Manager, who will walk you through the role and answer any questions you may have.

Please let us know if this date and time work for you, or feel free to suggest alternative availability.

Best regards,
Taylor Nguyen
Recruiting Coordinator
BrightWave Solutions

TONE: Professional, friendly, and welcoming

INTENT: Invite the candidate to interview and confirm availability

END OF EXAMPLE.

NOW GENERATE A NEW, ORIGINAL EMAIL USING THE EXACT SAME FORMAT.
START WITH SUBJECT: AND END WITH THE INTENT DESCRIPTION.
OUTPUT ONLY THE FOUR FIELDS.
"""


# =========================
# SETUP OUTPUT DIRECTORIES
# =========================
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# =========================
# HELPER FUNCTIONS
# =========================
def call_ollama(prompt, system):
    payload = {
        "model": MODEL_NAME,
        "system": system,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"]

def parse_email_robust(text):
    """
    FIXED: Robust parser using regex to handle multi-line content.
    Now more forgiving with whitespace and newlines.
    """
    text = text.strip()
    
    # Pattern: Match fields with flexible whitespace/newlines between them
    # Use non-greedy matching and allow multiple newlines
    pattern = r'SUBJECT:\s*(.+?)\s+BODY:\s*(.+?)\s+TONE:\s*(.+?)\s+INTENT:\s*(.+?)(?:\s*)$'
    
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        subject = match.group(1).strip()
        body = match.group(2).strip()
        tone = match.group(3).strip()
        intent = match.group(4).strip()
        
        # Validate all fields have content
        if subject and body and tone and intent:
            return {
                "subject": subject,
                "body": body,
                "tone": tone,
                "intent": intent
            }
    
    return None

def parse_email_fallback(text):
    """
    Fallback parser for cases where regex fails.
    More permissive but still handles multi-line content.
    """
    text = text.strip()
    lines = text.split('\n')
    
    fields = {"subject": "", "body": "", "tone": "", "intent": ""}
    current_field = None
    buffer = []
    
    for line in lines:
        # Check if this line starts a new field (case-insensitive, start of line)
        line_upper = line.strip().upper()
        
        if line_upper.startswith("SUBJECT:"):
            if current_field and buffer:
                fields[current_field] = "\n".join(buffer).strip()
            current_field = "subject"
            # Capture content on same line if present
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            buffer = [content] if content else []
            
        elif line_upper.startswith("BODY:"):
            if current_field and buffer:
                fields[current_field] = "\n".join(buffer).strip()
            current_field = "body"
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            buffer = [content] if content else []
            
        elif line_upper.startswith("TONE:"):
            if current_field and buffer:
                fields[current_field] = "\n".join(buffer).strip()
            current_field = "tone"
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            buffer = [content] if content else []
            
        elif line_upper.startswith("INTENT:"):
            if current_field and buffer:
                fields[current_field] = "\n".join(buffer).strip()
            current_field = "intent"
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            buffer = [content] if content else []
            
        else:
            # Continue accumulating content for current field
            if current_field:
                buffer.append(line)
    
    # Don't forget the last field
    if current_field and buffer:
        fields[current_field] = "\n".join(buffer).strip()
    
    # Validate completeness
    if all(fields.values()):
        return fields
    
    return None

def parse_email(text):
    """
    Try robust regex parser first, fall back to line-by-line parser.
    """
    result = parse_email_robust(text)
    if result:
        return result
    
    return parse_email_fallback(text)

# =========================
# GENERATION LOOP
# =========================
successful = 0
failed = 0

for i in range(1, NUM_EMAILS + 1):
    print(f"\nGenerating email {i}/{NUM_EMAILS}")
    success = False
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Attempt {attempt}")
        try:
            raw_output = call_ollama(USER_PROMPT, SYSTEM_PROMPT)
            
            # Save raw output to DEBUG folder
            debug_file = os.path.join(DEBUG_DIR, f"debug_email_{i:04d}_attempt_{attempt}.txt")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(raw_output)
            print(f"    DEBUG: Saved raw output to {debug_file}")
            
            email_data = parse_email(raw_output)
            
            if email_data:
                email_data["id"] = i
                filename = f"email_{i:04d}.json"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(email_data, f, indent=2, ensure_ascii=False)
                
                print(f"  ✅ Saved {filepath}")
                successful += 1
                success = True
                
                # Clean up debug files on success
                for att in range(1, attempt + 1):
                    try:
                        os.remove(os.path.join(DEBUG_DIR, f"debug_email_{i:04d}_attempt_{att}.txt"))
                    except:
                        pass
                break
            else:
                print("  ⚠ Format invalid, retrying...")
                # Print first 200 chars of output for quick debugging
                print(f"    First 200 chars: {raw_output[:200]}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(0.2)
    
    if not success:
        print(f"  ❌ Skipped email {i} after {MAX_RETRIES} attempts")
        print(f"  📋 Check debug files in '{DEBUG_DIR}' folder for raw outputs")
        failed += 1
    
    time.sleep(DELAY_SECONDS)

print(f"\n{'='*50}")
print(f"✅ Bulk email generation complete.")
print(f"   Successful: {successful}/{NUM_EMAILS}")
print(f"   Failed: {failed}/{NUM_EMAILS}")
if failed > 0:
    print(f"   📋 Debug files saved in '{DEBUG_DIR}' folder - check them to see what the model is actually generating")
print(f"{'='*50}")