
from fastapi import FastAPI
from sqlalchemy import text

from app.api.resumes import router as resumes_router
from app.api.career_copilot import router as career_copilot_router
from app.core.config import settings
from app.db.session import SessionLocal


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-agent AI Career Copilot powered by LangGraph, MCP, Groq, and PostgreSQL.",
    version="1.0.0",
)

app.include_router(resumes_router)
app.include_router(career_copilot_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    """Check whether the API can access PostgreSQL."""

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected",
        }

    except Exception as exc:
        # Do not expose database credentials or internal exception details.
        return {
            "status": "not_ready",
            "database": "unavailable",
            "error_type": type(exc).__name__,
        }
