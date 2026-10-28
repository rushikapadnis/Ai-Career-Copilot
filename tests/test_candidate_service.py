
from uuid import uuid4

from app.db.session import SessionLocal
from app.services.candidate_service import save_candidate_and_resume
from app.schemas.resume import (
    CandidateResumeProfile,
    EducationItem,
    ExperienceItem,
    ProjectItem,
)


def main():
    test_email = f"test-{uuid4().hex[:10]}@example.com"

    profile = CandidateResumeProfile(
        full_name="Test Candidate",
        email=test_email,
        phone=None,
        professional_summary="Data scientist with machine learning experience.",
        total_experience_years=3.0,
        skills=["Python", "Machine Learning", "SQL"],
        experience=[
            ExperienceItem(
                job_title="Data Scientist",
                company="Example Company",
                duration="2023-2026",
                responsibilities=["Built machine learning models"],
            )
        ],
        education=[
            EducationItem(
                degree="M.Tech Computer Science",
                institution="Example University",
                graduation_year=2019,
            )
        ],
        projects=[
            ProjectItem(
                name="Resume Intelligence",
                description="Extracts structured candidate information.",
                technologies=["Python", "LLM"],
            )
        ],
        suggested_target_roles=["Senior Data Scientist"],
    )

    resume_text = (
        "Test resume for database persistence. "
        "Skills: Python, Machine Learning, SQL."
    )

    with SessionLocal() as db:
        candidate, resume = save_candidate_and_resume(
            db=db,
            file_name="test_resume.pdf",
            resume_text=resume_text,
            profile=profile,
        )

        print("\n--- DATABASE SAVE SUCCESSFUL ---")
        print(f"Candidate ID: {candidate.id}")
        print(f"Candidate name: {candidate.full_name}")
        print(f"Candidate email: {candidate.email}")
        print(f"Resume ID: {resume.id}")
        print(f"Resume filename: {resume.file_name}")
        print(f"Resume linked to candidate ID: {resume.candidate_id}")
        print(f"Skills saved: {candidate.skills}")
        print(
            "Structured profile saved:",
            bool(resume.extracted_profile),
        )


if __name__ == "__main__":
    main()
