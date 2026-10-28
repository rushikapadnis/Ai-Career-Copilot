
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.models import Application, CandidateProfile, Job
from app.db.session import SessionLocal

mcp = FastMCP("career-workspace")


@mcp.tool()
def get_candidate_profile(candidate_id: int) -> dict:
    """Get a candidate's profile from the career workspace."""
    with SessionLocal() as db:
        candidate = db.get(CandidateProfile, candidate_id)

        if candidate is None:
            return {"error": "Candidate not found"}

        return {
            "candidate_id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "experience_years": candidate.experience_years,
            "target_role": candidate.target_role,
            "preferred_location": candidate.preferred_location,
            "skills": candidate.skills or [],
        }


@mcp.tool()
def list_jobs(limit: int = 20) -> dict:
    """List jobs currently stored in the career workspace."""
    limit = max(1, min(limit, 100))

    with SessionLocal() as db:
        jobs = db.scalars(
            select(Job).order_by(Job.created_at.desc()).limit(limit)
        ).all()

        return {
            "count": len(jobs),
            "jobs": [
                {
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "source": job.source,
                    "job_url": job.job_url,
                }
                for job in jobs
            ],
        }


@mcp.tool()
def save_job(
    candidate_id: int,
    job_id: int,
    notes: str = "",
) -> dict:
    """Save an existing job for a candidate, avoiding duplicate applications."""
    with SessionLocal() as db:
        candidate = db.get(CandidateProfile, candidate_id)
        if candidate is None:
            return {"error": "Candidate not found"}

        job = db.get(Job, job_id)
        if job is None:
            return {"error": "Job not found"}

        existing = db.scalar(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_id == job_id,
            )
        )

        if existing is not None:
            return {
                "message": "Job is already saved for this candidate",
                "application_id": existing.id,
                "status": existing.status,
            }

        application = Application(
            candidate_id=candidate_id,
            job_id=job_id,
            status="saved",
            notes=notes or None,
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        return {
            "message": "Job saved successfully",
            "application_id": application.id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": application.status,
        }


@mcp.tool()
def update_application_status(
    application_id: int,
    status: str,
) -> dict:
    """Update an application status to a supported career-tracking state."""
    allowed_statuses = {
        "saved",
        "applied",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    }

    normalized_status = status.strip().lower()
    if normalized_status not in allowed_statuses:
        return {
            "error": "Invalid status",
            "allowed_statuses": sorted(allowed_statuses),
        }

    with SessionLocal() as db:
        application = db.get(Application, application_id)

        if application is None:
            return {"error": "Application not found"}

        application.status = normalized_status
        db.commit()
        db.refresh(application)

        return {
            "message": "Application status updated",
            "application_id": application.id,
            "status": application.status,
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
