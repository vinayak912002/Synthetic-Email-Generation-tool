import csv

# ===== CONFIG =====
INPUT_CSV = "E:\\Synthetic-Email-Generation-tool-main\\Candidate_application\\candidate_application.csv"   # your generated file
OUTPUT_CSV = "E:\\Synthetic-Email-Generation-tool-main\\Candidate_application\\candidate_application_labeled.csv"
LABEL_NAME = "candidate_application"

# ===== PROCESS =====
with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.DictReader(infile)
    writer = csv.writer(outfile)

    # Write new header
    writer.writerow(["label", "text"])

    for row in reader:
        subject = row.get("subject", "").strip()
        body = row.get("body", "").strip()

        # Combine subject + body (ATS-style)
        combined_text = f"Subject: {subject}\n\n{body}"

        writer.writerow([LABEL_NAME, combined_text])

print("✅ Dataset successfully labeled and saved:", OUTPUT_CSV)
