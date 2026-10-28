from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    experience_years: Mapped[int] = mapped_column(
        Integer, default=0
    )
    target_role: Mapped[str] = mapped_column(String(150))
    preferred_location: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    skills: Mapped[list] = mapped_column(
        JSON, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id"),
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255))
    extracted_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    extracted_profile: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    source: Mapped[str] = mapped_column(String(100))
    job_url: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id"),
        index=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="saved"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )