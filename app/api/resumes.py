
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.resume import CandidateResumeProfile
from app.services.candidate_service import save_candidate_and_resume
from app.services.resume_intelligence import (
    ResumeIntelligenceError,
    extract_candidate_profile,
)
from app.services.resume_parser import (
    MAX_FILE_SIZE_BYTES,
    ResumeParsingError,
    extract_resume_text,
)

from sqlalchemy import select

from app.db.models import CandidateProfile, Resume

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CandidateProfile, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    resumes = db.scalars(
        select(Resume)
        .where(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
    ).all()

    return {
        "candidate_id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "experience_years": candidate.experience_years,
        "target_role": candidate.target_role,
        "preferred_location": candidate.preferred_location,
        "skills": candidate.skills or [],
        "created_at": candidate.created_at,
        "resumes": [
            {
                "resume_id": resume.id,
                "file_name": resume.file_name,
                "created_at": resume.created_at,
            }
            for resume in resumes
        ],
    }


@router.get("/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    return {
        "resume_id": resume.id,
        "candidate_id": resume.candidate_id,
        "file_name": resume.file_name,
        "extracted_profile": resume.extracted_profile,
        "created_at": resume.created_at,
    }


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A resume filename is required.",
        )

    try:
        # Read at most 5 MB + 1 byte to enforce the upload limit.
        file_bytes = file.file.read(MAX_FILE_SIZE_BYTES + 1)

        resume_text = extract_resume_text(
            file_name=file.filename,
            file_bytes=file_bytes,
        )

        profile: CandidateResumeProfile = extract_candidate_profile(
            resume_text
        )

        candidate, resume = save_candidate_and_resume(
            db=db,
            file_name=file.filename,
            resume_text=resume_text,
            profile=profile,
        )

        return {
            "message": "Resume uploaded and processed successfully.",
            "candidate_id": candidate.id,
            "resume_id": resume.id,
            "candidate": {
                "full_name": candidate.full_name,
                "email": candidate.email,
                "experience_years": candidate.experience_years,
                "target_role": candidate.target_role,
                "skills": candidate.skills or [],
            },
            "resume_profile": profile.model_dump(mode="json"),
        }

    except ResumeParsingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ResumeIntelligenceError as exc:
        logger.warning("Resume intelligence failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Resume text was extracted, but AI profile extraction failed. "
                   "Check the Groq configuration and retry.",
        ) from exc

    except SQLAlchemyError as exc:
        logger.exception("Database error while saving resume")
        raise HTTPException(
            status_code=500,
            detail="Unable to save the resume to the database.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected resume upload error")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the resume.",
        ) from exc

    finally:
        file.file.close()
