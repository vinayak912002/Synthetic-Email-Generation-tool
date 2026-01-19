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
OUTPUT_CSV = "job_application.csv"
DEBUG_DIR = "emails/debug"
LOG_FILE = "generation_history.log"  # <--- NEW LOG FILE
NUM_EMAILS = 500       
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
SYSTEM_PROMPT = """You are a job candidate email generator. You MUST output ONLY the four fields: SUBJECT, BODY, TONE, INTENT. 
Do not add explanations, preambles, or markdown. Follow the exact format specified."""

BASE_USER_PROMPT = """Generate a unique job application email from a candidate applying for a {role} position. 
The candidate describes themselves as {adjective}.

REQUIREMENTS:
- Invent realistic fictional names (candidate, company, hiring manager)
- Mention specific skills relevant to {role}
- Professional, respectful tone
- No double quotes anywhere
- Address manager by name (or 'Hiring Manager' if generic)
- Ask for an interview
- Professional closing

CRITICAL:
- You MUST output ONLY the four fields shown below
- Use the EXACT same format and field order as the example

EXAMPLE OUTPUT:

SUBJECT: Application for Marketing Manager - Alex Rivera

BODY:
Dear Ms. Johnson,

I am writing to express my strong interest in the Marketing Manager position at CloudNine Systems. With over five years of experience in digital strategy and content creation, I am confident in my ability to drive brand growth for your team.

My background includes successfully managing SEO campaigns and increasing social media engagement by 40%. I admire CloudNine's recent work in the tech sector and would love to bring my creative approach to your projects.

I have attached my resume for your review. Thank you for your time and consideration.

Sincerely,
Alex Rivera

TONE: Confident, professional, and enthusiastic

INTENT: Apply for a job and highlight relevant experience

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