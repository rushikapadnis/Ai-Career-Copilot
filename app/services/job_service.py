
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job


def save_discovered_jobs(
    db: Session,
    jobs: list[dict],
) -> dict:
    """Upsert real provider jobs into PostgreSQL."""

    inserted = 0
    updated = 0

    try:
        for item in jobs:
            external_id = str(item.get("external_id", "")).strip()

            if not external_id:
                continue

            existing = db.scalar(
                select(Job).where(
                    Job.external_id == external_id
                )
            )

            values = {
                "title": item.get("title") or "Untitled",
                "company": item.get("company") or "Unknown",
                "location": item.get("location"),
                "description": item.get("description"),
                "source": item.get("source") or "Remotive",
                "job_url": item.get("job_url"),
            }

            if existing:
                for field, value in values.items():
                    setattr(existing, field, value)
                updated += 1
            else:
                db.add(
                    Job(
                        external_id=external_id,
                        **values,
                    )
                )
                inserted += 1

        db.commit()

        return {
            "inserted": inserted,
            "updated": updated,
            "total_processed": inserted + updated,
        }

    except Exception:
        db.rollback()
        raise
