
from pydantic import BaseModel, Field ,field_validator


class ExperienceItem(BaseModel):
    job_title: str | None = None
    company: str | None = None
    duration: str | None = None
    responsibilities: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str | None = None
    institution: str | None = None
    graduation_year: str | None = None

    @field_validator("graduation_year", mode="before")
    @classmethod
    def normalize_graduation_year(cls, value):
        if value is None:
            return None

        return str(value)


class ProjectItem(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class CandidateResumeProfile(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None

    professional_summary: str | None = None
    total_experience_years: float | None = Field(
        default=None, ge=0, le=60
    )

    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(
        default_factory=list
    )
    education: list[EducationItem] = Field(
        default_factory=list
    )
    projects: list[ProjectItem] = Field(
        default_factory=list
    )

    suggested_target_roles: list[str] = Field(
        default_factory=list
    )
