
import asyncio
import json

from langgraph.graph import END, START, StateGraph
from typing import Any, TypedDict

from app.db.session import SessionLocal
from app.services.job_matching_service import match_candidate_to_jobs


class JobMatchingState(TypedDict, total=False):
    candidate_id: int
    limit: int
    matches: list[dict[str, Any]]
    jobs_evaluated: int
    error: str



def match_jobs_node(state: JobMatchingState) -> dict:
    candidate_id = state.get("candidate_id")

    if candidate_id is None:
        return {
            "error": "candidate_id is required.",
            "matches": [],
        }

    result = run_job_matching(
        candidate_id=candidate_id,
        limit=state.get("limit", 10),
    )

    if result.get("error"):
        return {
            "error": result["error"],
            "matches": [],
            "jobs_evaluated": 0,
        }

    matches = result.get("matches", [])

    print(f"[Job Matching Agent] Returning {len(matches)} ranked matches.")

    return {
        "matches": matches,
        "jobs_evaluated": result.get("jobs_evaluated", 0),
        "error": "",
    }



def run_job_matching(candidate_id: int, limit: int = 10) -> dict:
    """Run job matching directly for reuse by the main orchestrator."""
    try:
        with SessionLocal() as db:
            result = match_candidate_to_jobs(
                db=db,
                candidate_id=candidate_id,
                limit=limit,
            )

        return result

    except Exception as exc:
        return {
            "candidate_id": candidate_id,
            "jobs_evaluated": 0,
            "matches": [],
            "error": str(exc),
        }


builder = StateGraph(JobMatchingState)
builder.add_node("match_jobs", match_jobs_node)
builder.add_edge(START, "match_jobs")
builder.add_edge("match_jobs", END)

job_matching_graph = builder.compile()


async def main():
    # Replace 1 with the candidate ID printed after resume upload.
    candidate_id = 1

    result = await job_matching_graph.ainvoke({
        "candidate_id": candidate_id,
        "limit": 10,
    })

    print("\n--- JOB MATCHING RESULTS ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
