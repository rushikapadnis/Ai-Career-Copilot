
import re
from html import unescape

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CandidateProfile, Job


# Initial skill vocabulary for transparent, rule-based matching.
# Extend this list as the project supports more job categories.
SKILL_VOCABULARY = [
    "python",
    "java",
    "sql",
    "machine learning",
    "deep learning",
    "data science",
    "natural language processing",
    "nlp",
    "computer vision",
    "generative ai",
    "agentic ai",
    "llm",
    "rag",
    "langchain",
    "langgraph",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "pandas",
    "numpy",
    "spark",
    "databricks",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "fastapi",
    "postgresql",
    "redis",
    "vector database",
    "statistics",
    "data analysis",
    "react",
    "javascript",
    "typescript",
    "ruby",
    "rails",
]


def normalize_text(value: str | None) -> str:
    """Normalize HTML and text for basic keyword comparison."""
    if not value:
        return ""

    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = value.lower()

    return re.sub(r"\s+", " ", value).strip()


def normalize_skill(skill: str) -> str:
    """Normalize a skill name."""
    return normalize_text(skill).strip()


def extract_job_skills(job_text: str) -> set[str]:
    """Find vocabulary terms explicitly mentioned in a job listing."""
    text = normalize_text(job_text)
    found = set()

    for skill in SKILL_VOCABULARY:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, text):
            found.add(skill)

    return found


def calculate_job_match(
    candidate_skills: list[str],
    target_role: str | None,
    job: Job,
) -> dict:
    """
    Calculate an explainable heuristic match score.

    This is a keyword-based estimate, not a probability of being hired.
    """
    profile_skills = {
        normalize_skill(skill)
        for skill in candidate_skills
        if isinstance(skill, str) and skill.strip()
    }

    # Map known aliases to canonical names.
    aliases = {
        "nlp": "natural language processing",
        "llm": "generative ai",
    }

    profile_skills = {
        aliases.get(skill, skill)
        for skill in profile_skills
    }

    job_text = normalize_text(
        f"{job.title or ''} {job.description or ''}"
    )

    job_skills = extract_job_skills(job_text)

    matched_skills = sorted(profile_skills & job_skills)
    missing_skills = sorted(job_skills - profile_skills)

    if job_skills:
        skill_score = (
            len(matched_skills) / len(job_skills)
        ) * 80
    else:
        skill_score = 0.0

    target_tokens = set(
        re.findall(r"\b[a-z0-9+#.]+\b", normalize_text(target_role))
    )
    title_tokens = set(
        re.findall(r"\b[a-z0-9+#.]+\b", normalize_text(job.title))
    )

    # Ignore generic words that add little role information.
    generic_words = {
        "and", "or", "the", "a", "an", "for", "with",
        "engineer", "engineering", "senior", "junior",
        "lead", "manager", "specialist",
    }

    target_tokens -= generic_words
    title_tokens -= generic_words

    if target_tokens:
        role_score = (
            len(target_tokens & title_tokens) / len(target_tokens)
        ) * 20
    else:
        role_score = 0.0

    score = round(min(100.0, skill_score + role_score), 2)

    return {
        "job_id": job.id,
        "external_id": job.external_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "source": job.source,
        "job_url": job.job_url,
        "match_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_coverage_percent": (
            round(len(matched_skills) / len(job_skills) * 100, 2)
            if job_skills
            else None
        ),
        "scoring_note": (
            "Heuristic based on detected job skills and target-role "
            "title overlap. Not a probability of hiring."
        ),
    }


def match_candidate_to_jobs(
    db: Session,
    candidate_id: int,
    limit: int = 10,
) -> dict:
    """Rank persisted jobs against a candidate's saved profile."""

    candidate = db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.id == candidate_id
        )
    )

    if candidate is None:
        return {
            "error": f"Candidate {candidate_id} was not found."
        }

    raw_skills = candidate.skills or []

    if isinstance(raw_skills, dict):
        raw_skills = list(raw_skills.keys())

    if not isinstance(raw_skills, list):
        raw_skills = []

    candidate_skills = [
        skill for skill in raw_skills
        if isinstance(skill, str)
    ]

    if not candidate_skills and not candidate.target_role:
        return {
            "error": (
                "The candidate profile has no skills or target role. "
                "Upload or update a resume profile first."
            )
        }

    jobs = db.scalars(
        select(Job).order_by(Job.created_at.desc())
    ).all()

    results = [
        calculate_job_match(
            candidate_skills=candidate_skills,
            target_role=candidate.target_role,
            job=job,
        )
        for job in jobs
    ]

    results.sort(
        key=lambda item: item["match_score"],
        reverse=True,
    )

    limit = max(1, min(int(limit), 50))

    return {
        "candidate_id": candidate.id,
        "target_role": candidate.target_role,
        "candidate_skills": candidate_skills,
        "jobs_evaluated": len(results),
        "matches": results[:limit],
        "scoring_note": (
            "Scores are heuristic ranking signals, not hiring "
            "probabilities. The skill vocabulary is limited and may "
            "miss relevant requirements."
        ),
    }
