
from pathlib import Path

from app.services.resume_parser import extract_resume_text


resume_path = Path("data/resume_datascience.pdf")

resume_text = extract_resume_text(
    resume_path.name,
    resume_path.read_bytes(),
)

print("\n--- EXTRACTED RESUME TEXT ---\n")
print(resume_text)
print("\n--- END OF RESUME TEXT ---")
