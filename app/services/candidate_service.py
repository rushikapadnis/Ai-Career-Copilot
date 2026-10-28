
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CandidateProfile, Resume
from app.schemas.resume import CandidateResumeProfile


def save_candidate_and_resume(
    db: Session,
    file_name: str,
    resume_text: str,
    profile: CandidateResumeProfile,
) -> tuple[CandidateProfile, Resume]:
    """
    Save the extracted candidate profile and resume in one transaction.

    If a candidate with the same email already exists, update that
    candidate instead of creating a duplicate.
    """
    email = profile.email.strip().lower() if profile.email else None

    try:
        candidate = None

        if email:
            candidate = db.scalar(
                select(CandidateProfile).where(
                    CandidateProfile.email == email
                )
            )

        if candidate is None:
            candidate = CandidateProfile(
                full_name=profile.full_name,
                email=email,
                experience_years=profile.total_experience_years,
                target_role=(
                    profile.suggested_target_roles[0]
                    if profile.suggested_target_roles
                    else None
                ),
                skills=profile.skills,
            )
            db.add(candidate)
            db.flush()
        else:
            # Refresh known fields without overwriting them with missing data.
            if profile.full_name:
                candidate.full_name = profile.full_name

            if profile.total_experience_years is not None:
                candidate.experience_years = profile.total_experience_years

            if profile.suggested_target_roles:
                candidate.target_role = profile.suggested_target_roles[0]

            if profile.skills:
                candidate.skills = profile.skills

        resume = Resume(
            candidate_id=candidate.id,
            file_name=file_name,
            extracted_text=resume_text,
            extracted_profile=profile.model_dump(mode="json"),
        )
        db.add(resume)
        db.flush()

        db.commit()
        db.refresh(candidate)
        db.refresh(resume)

        return candidate, resume

    except Exception:
        db.rollback()
        raise
