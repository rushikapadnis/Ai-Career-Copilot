
from pathlib import Path

from app.services.resume_parser import extract_resume_text
from app.services.resume_intelligence import (
    extract_candidate_profile,
)


def main():
    resume_path = Path("data/resume_datascience.pdf")

    if not resume_path.exists():
        raise FileNotFoundError(
            "Add a test resume at data/resume_datascience.pdf "
            "before running this test."
        )

    # Step 1: Extract text from the resume.
    resume_text = extract_resume_text(
        resume_path.name,
        resume_path.read_bytes(),
    )

    print("\nResume text extracted successfully.")
    print(f"Extracted characters: {len(resume_text)}")

    # Step 2: Extract a structured profile using Groq.
    profile = extract_candidate_profile(resume_text)

    # Step 3: Display the validated profile.
    print("\n--- CANDIDATE PROFILE ---")
    print(profile.model_dump_json(indent=2))
    print("\n--- EXTRACTION COMPLETED ---")


if __name__ == "__main__":
    main()
