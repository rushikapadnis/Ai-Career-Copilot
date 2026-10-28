
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.career_copilot_graph import career_copilot_graph


router = APIRouter(prefix="/api/career-copilot", tags=["Career Copilot"])


class CareerCopilotRequest(BaseModel):
    candidate_id: int = Field(gt=0)
    search: str = Field(default="data scientist", max_length=200)
    category: str = Field(default="", max_length=100)
    discovery_limit: int = Field(default=10, ge=1, le=20)
    matching_limit: int = Field(default=10, ge=1, le=50)


@router.post("/run")
async def run_career_copilot(
    request: CareerCopilotRequest,
) -> dict[str, Any]:
    try:
        result = await career_copilot_graph.ainvoke({
            "candidate_id": request.candidate_id,
            "search": request.search,
            "category": request.category,
            "discovery_limit": request.discovery_limit,
            "matching_limit": request.matching_limit,
            "errors": [],
        })

        report = result.get("report")

        if not report:
            raise HTTPException(
                status_code=500,
                detail="The workflow did not produce a final report.",
            )

        return {
            "status": "completed",
            "report": report,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Career Copilot workflow failed: {exc}",
        ) from exc
