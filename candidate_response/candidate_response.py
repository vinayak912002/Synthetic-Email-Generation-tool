import requests
import json
import os
import time
import re
import csv
import hashlib
import random

# =========================
# CONFIGURATION
# =========================
MODEL_NAME = "llama3.2:3b-instruct-q4_0" # Ensure you have this model
OLLAMA_URL = "http://localhost:11434/api/generate"
OUTPUT_CSV = "E:\\Synthetic-Email-Generation-tool-main\\candidate_response\\candidate_response.csv"
DEBUG_DIR = "E:\\Synthetic-Email-Generation-tool-main\\candidate_response\\debug"
LOG_FILE = "E:\\Synthetic-Email-Generation-tool-main\\candidate_response\\candidate_response_history.log"  # <--- NEW LOG FILE
NUM_EMAILS = 600       
DELAY_SECONDS = 0.1      
MAX_RETRIES = 3          

# =========================
# DYNAMIC VARIABLES
# =========================
ROLES = [
    "Software Engineer", "Data Scientist", "Marketing Manager", "Sales Representative",
    "Graphic Designer", "Nurse", "Project Manager", "Accountant", "Teacher", "Chef",
    "Electrician", "Customer Support Agent", "HR Specialist", "Product Owner",
    "Social Media Manager", "Financial Analyst", "Executive Assistant", "Mechanic",
    "UX/UI Designer", "Operations Manager", "Copywriter", "Receptionist", 
    "Civil Engineer", "DevOps Specialist", "Cybersecurity Analyst", "Legal Secretary",
    "Warehouse Supervisor", "Phlebotomist", "Paralegal", "Event Planner", 
    "Supply Chain Analyst", "Real Estate Agent", "Dental Hygienist", "Architect",
    "Video Editor", "Content Strategist", "IT Support Technician", "Plumber",
    "Bank Teller", "Pharmacist", "Data Entry Clerk", "SEO Specialist", 
    "Flight Attendant", "QA Tester", "Cloud Architect", "Business Analyst",
    "Network Engineer", "Systems Administrator", "Office Manager", "Editor",
    "Interior Designer", "Landscape Architect", "Sustainability Consultant",
    "Truck Driver", "Security Guard", "Bartender", "Web Developer",
    "Physical Therapist", "Occupational Therapist", "Speech Pathologist",
    "Radiologic Technologist", "Case Manager", "Recruiter", "PR Specialist",
    "Digital Marketer", "E-commerce Manager", "Mobile App Developer",
    "Game Designer", "Animator", "Sound Engineer", "Translator",
    "Database Administrator", "Machine Learning Engineer", "Actuary",
    "Investment Banker", "Mortgage Broker", "Loan Officer", "Insurance Agent",
    "Underwriter", "Safety Inspector", "Construction Foreman", "Welder",
    "CNC Machinist", "HVAC Technician", "Automotive Technician", "Pilot",
    "Logistician", "Brand Ambassador", "Museum Curator", "Librarian",
    "Non-profit Coordinator", "Grant Writer", "Policy Analyst",
    "Sociologist", "Urban Planner", "Flight Instructor", "Personal Trainer"
]

ADJECTIVES = [
    "passionate", "experienced", "entry-level", "motivated", "detail-oriented",
    "innovative", "dedicated", "strategic", "creative", "results-driven",
    "enthusiastic", "highly-organized", "resourceful", "proactive",
    "technically-proficient", "adaptable", "hard-working", "analytical",
    "collaborative", "forward-thinking", "self-motivated", "disciplined",
    "client-focused", "versatile", "methodical", "ambitious", "reliable",
    "dynamic", "energetic", "articulate", "knowledgeable", "empathetic",
    "diligent", "professional", "resilient", "determined", "skilled",
    "qualified", "fast-learning", "independent"
]

# =========================
# PROMPTS
# =========================
SYSTEM_PROMPT = """You are an HR email generator. You MUST output ONLY the four fields: SUBJECT, BODY, TONE, INTENT.
Do not add explanations, preambles, markdown, or extra text.
Follow the exact format specified.
"""

BASE_USER_PROMPT = """Generate a realistic candidate response acknowledgment email sent FROM a company TO a candidate.
This email is sent after the candidate has replied or responded to a previous hiring-related communication.

CONTEXT:
- The response is regarding a {role} position
- The candidate described themselves as {adjective}

REQUIREMENTS:
- Invent realistic fictional names for the candidate, company, and HR representative
- The candidate name and HR representative name MUST be different in every email
- Do NOT reuse the same HR name or candidate name across emails
- Thank the candidate for their response
- Express appreciation for the candidate’s interest in the position
- Do NOT confirm interview scheduling, selection, or rejection
- Professional, neutral, ATS-style tone
- Short, realistic corporate email
- No double quotes anywhere
- Professional closing

CRITICAL:
- You MUST output ONLY the four fields shown below
- Use the EXACT same format and field order as the example

EXAMPLE OUTPUT:

SUBJECT: Thank You for Your Response | Software Engineer Position

BODY:
Dear Michael Turner,

Thank you for your response regarding the Software Engineer position at Apex Technologies.

We appreciate your continued interest in this role and your engagement in the hiring process. Our team has noted your response and will take it into consideration as we proceed.

Thank you for your interest in joining Apex Technologies.

Kind regards,
Rachel Evans  
Recruitment Operations Manager  
Apex Technologies

TONE: Professional, courteous, and neutral

INTENT: Acknowledge candidate response

END OF EXAMPLE.

NOW GENERATE A NEW EMAIL.


"""

# =========================
# SETUP
# =========================
os.makedirs(DEBUG_DIR, exist_ok=True)

# Initialize CSV with headers if it doesn't exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject", "body", "tone", "intent"])
        writer.writeheader()

# Load existing hashes to avoid duplicates
seen_hashes = set()
start_id = 1

if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        start_id = len(rows) + 1
        for row in rows:
            if "body" in row and row["body"]:
                h = hashlib.md5(row["body"].encode('utf-8')).hexdigest()
                seen_hashes.add(h)

print(f"RESUMING from ID {start_id} (Loaded {len(seen_hashes)} existing unique emails)")

# =========================
# HELPER FUNCTIONS
# =========================
def log_event(message):
    """Logs success/fail events to a text file with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Logging error: {e}")

def call_ollama(prompt, system):
    payload = {
        "model": MODEL_NAME,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {
    "temperature": 0.8,
    "top_p": 0.9,
}
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=40)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"    API Error: {e}")
        return None

def parse_email(text):
    text = text.strip()
    # Robust Regex Pattern
    pattern = r'SUBJECT:\s*(.+?)\s+BODY:\s*(.+?)\s+TONE:\s*(.+?)\s+INTENT:\s*(.+?)(?:\s*)$'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return {
            "subject": match.group(1).strip(),
            "body": match.group(2).strip(),
            "tone": match.group(3).strip(),
            "intent": match.group(4).strip()
        }
    return None

# =========================
# MAIN LOOP
# =========================
current_id = start_id
total_success = 0

print(f"Starting generation of {NUM_EMAILS} emails...")
print(f"Saving data to: {OUTPUT_CSV}")
print(f"Saving logs to: {LOG_FILE}")
print("-" * 50)

log_event(f"--- STARTING SCRIPT SESSION FROM ID {current_id} ---")

while current_id <= NUM_EMAILS:
    
    # Optional Manual Stop Check
    if os.path.exists("stop.txt"):
        print("\n🛑 Stop file detected. Closing safely...")
        log_event("MANUAL STOP: stop.txt detected.")
        break

    print(f"Generating ID {current_id}/{NUM_EMAILS}...", end="", flush=True)
    
    # Randomize Prompt
    role = random.choice(ROLES)
    adj = random.choice(ADJECTIVES)
    current_prompt = BASE_USER_PROMPT.format(role=role, adjective=adj)
    
    success = False
    
    for attempt in range(1, MAX_RETRIES + 1):
        raw_output = call_ollama(current_prompt, SYSTEM_PROMPT)
        
        if not raw_output:
            continue 
            
        email_data = parse_email(raw_output)
        
        if email_data:
            # Check duplicates
            body_hash = hashlib.md5(email_data["body"].encode('utf-8')).hexdigest()
            
            if body_hash in seen_hashes:
                print(f" [Duplicate detected] ", end="", flush=True)
                continue 
            
            # SUCCESS
            email_data["id"] = current_id
            seen_hashes.add(body_hash)
            
            # Save to CSV
            with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "subject", "body", "tone", "intent"])
                writer.writerow(email_data)
            
            # Log Success
            log_event(f"SUCCESS: Email ID {current_id} saved. (Role: {role})")
            
            print(" ✅ Saved")
            current_id += 1
            total_success += 1
            success = True
            break 
        else:
            # Save debug file on failure
            with open(os.path.join(DEBUG_DIR, f"fail_{current_id}_att{attempt}.txt"), "w", encoding="utf-8") as f:
                f.write(raw_output)
            print(f" ⚠ Parse Fail", end="", flush=True)
    
    if not success:
        # Log Failure
        log_event(f"SKIPPED: Email ID {current_id} failed after {MAX_RETRIES} attempts.")
        print(" ❌ Failed 3 attempts (skipping ID)")
        current_id += 1 

    time.sleep(DELAY_SECONDS)

print("=" * 50)
print(f"Job Complete/Stopped. Generated {total_success} new unique emails.")
log_event(f"--- SCRIPT STOPPED. TOTAL NEW EMAILS: {total_success} ---")