
import json

from sqlalchemy import select

from app.db.models import CandidateProfile
from app.db.session import SessionLocal
from app.services.job_matching_service import match_candidate_to_jobs


def main():
    with SessionLocal() as db:
        candidates = db.scalars(
            select(CandidateProfile).order_by(
                CandidateProfile.id.desc()
            )
        ).all()

        if not candidates:
            print(
                "No candidate profiles found. Upload a resume first."
            )
            return

        candidate = candidates[0]

        result = match_candidate_to_jobs(
            db=db,
            candidate_id=candidate.id,
            limit=10,
        )

        print("\n--- JOB MATCHING RESULTS ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
