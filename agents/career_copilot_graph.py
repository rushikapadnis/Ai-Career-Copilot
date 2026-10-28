
import asyncio
import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.db.session import SessionLocal
from app.services.job_service import save_discovered_jobs

from agents.job_discovery_agent import call_job_discovery_mcp
from agents.job_matching_agent import run_job_matching
from agents.resume_optimization_agent import run_resume_optimization
from agents.quality_review_agent import run_quality_review


class CareerCopilotState(TypedDict, total=False):
    candidate_id: int
    search: str
    category: str
    discovery_limit: int
    matching_limit: int

    discovered_jobs: list[dict[str, Any]]
    persistence: dict[str, Any]
    matches: list[dict[str, Any]]
    jobs_evaluated: int
    selected_job_id: int | None
    suggestions: dict[str, Any]
    review: dict[str, Any]
    report: dict[str, Any]
    error: str
    errors: list[str]


# ---------------------------------------------------------
# NODE 1: Discover real jobs through MCP and save to PostgreSQL
# ---------------------------------------------------------
async def discover_jobs_node(state: CareerCopilotState) -> dict:
    print("\n[Career Copilot] Step 1: Discovering live jobs...")

    try:
        result = await call_job_discovery_mcp(
            search=state.get("search", "data scientist"),
            category=state.get("category", ""),
            limit=state.get("discovery_limit", 10),
        )

        jobs = result.get("jobs", [])

        with SessionLocal() as db:
            persistence = save_discovered_jobs(db, jobs)

        print(f"[Career Copilot] Discovered {len(jobs)} jobs.")
        print(f"[Career Copilot] PostgreSQL: {persistence}")

        return {
            "discovered_jobs": jobs,
            "persistence": persistence,
            "error": "",
            "errors": [],
        }

    except Exception as exc:
        message = f"Job discovery failed: {exc}"
        print(f"[Career Copilot] {message}")

        return {
            "discovered_jobs": [],
            "persistence": {},
            "error": message,
            "errors": [message],
        }


# ---------------------------------------------------------
# NODE 2: Match the candidate against saved jobs
# ---------------------------------------------------------
def match_jobs_node(state: CareerCopilotState) -> dict:
    print("\n[Career Copilot] Step 2: Matching candidate to jobs...")

    candidate_id = state.get("candidate_id")

    if candidate_id is None:
        message = "candidate_id is required."
        return {
            "matches": [],
            "jobs_evaluated": 0,
            "selected_job_id": None,
            "error": message,
            "errors": state.get("errors", []) + [message],
        }

    try:
        result = run_job_matching(
            candidate_id=candidate_id,
            limit=state.get("matching_limit", 10),
        )

        if result.get("error"):
            message = f"Job matching failed: {result['error']}"
            return {
                "matches": [],
                "jobs_evaluated": 0,
                "selected_job_id": None,
                "error": message,
                "errors": state.get("errors", []) + [message],
            }

        matches = result.get("matches", [])

        # Only select a job with a positive heuristic score.
        best_match = next(
            (
                match
                for match in matches
                if (match.get("match_score") or 0) > 0
            ),
            None,
        )

        selected_job_id = (
            best_match.get("job_id") if best_match else None
        )

        print(f"[Career Copilot] Evaluated {len(matches)} jobs.")
        print(f"[Career Copilot] Selected job ID: {selected_job_id}")

        return {
            "matches": matches,
            "jobs_evaluated": result.get("jobs_evaluated", len(matches)),
            "selected_job_id": selected_job_id,
            "error": "",
        }

    except Exception as exc:
        message = f"Job matching failed: {exc}"
        print(f"[Career Copilot] {message}")

        return {
            "matches": [],
            "jobs_evaluated": 0,
            "selected_job_id": None,
            "error": message,
            "errors": state.get("errors", []) + [message],
        }


# ---------------------------------------------------------
# NODE 3: Optimize resume for the best matching job
# ---------------------------------------------------------
def optimize_resume_node(state: CareerCopilotState) -> dict:
    print("\n[Career Copilot] Step 3: Optimizing resume...")

    candidate_id = state.get("candidate_id")
    job_id = state.get("selected_job_id")

    if job_id is None:
        message = (
            "No positive-scoring job match was found. "
            "Resume optimization was skipped."
        )
        print(f"[Career Copilot] {message}")

        return {
            "suggestions": {},
            "error": message,
            "errors": state.get("errors", []) + [message],
        }

    try:
        result = run_resume_optimization(
            candidate_id=candidate_id,
            job_id=job_id,
        )

        if result.get("error"):
            message = f"Resume optimization failed: {result['error']}"
            return {
                "suggestions": {},
                "error": message,
                "errors": state.get("errors", []) + [message],
            }

        suggestions = result.get("suggestions", {})

        print("[Career Copilot] Resume recommendations generated.")

        return {
            "suggestions": suggestions,
            "error": "",
        }

    except Exception as exc:
        message = f"Resume optimization failed: {exc}"
        print(f"[Career Copilot] {message}")

        return {
            "suggestions": {},
            "error": message,
            "errors": state.get("errors", []) + [message],
        }


# ---------------------------------------------------------
# NODE 4: Quality-review resume recommendations
# ---------------------------------------------------------
def review_resume_node(state: CareerCopilotState) -> dict:
    print("\n[Career Copilot] Step 4: Reviewing recommendation quality...")

    suggestions = state.get("suggestions", {})

    if not suggestions:
        return {
            "review": {},
            "errors": state.get("errors", []),
        }

    try:
        result = run_quality_review(suggestions)

        if result.get("error"):
            message = f"Quality review failed: {result['error']}"
            return {
                "review": result.get("review", {}),
                "error": message,
                "errors": state.get("errors", []) + [message],
            }

        print(
            "[Career Copilot] Review status:",
            result.get("review", {}).get("status", "UNKNOWN"),
        )

        return {
            "review": result.get("review", {}),
            "error": "",
        }

    except Exception as exc:
        message = f"Quality review failed: {exc}"
        print(f"[Career Copilot] {message}")

        return {
            "review": {},
            "error": message,
            "errors": state.get("errors", []) + [message],
        }


# ---------------------------------------------------------
# NODE 5: Assemble the final report
# ---------------------------------------------------------
def build_report_node(state: CareerCopilotState) -> dict:
    print("\n[Career Copilot] Step 5: Building final report...")

    return {
        "report": {
            "candidate_id": state.get("candidate_id"),
            "discovery": {
                "provider": "Remotive",
                "jobs_discovered": len(
                    state.get("discovered_jobs", [])
                ),
                "persistence": state.get("persistence", {}),
            },
            "job_matching": {
                "jobs_evaluated": state.get("jobs_evaluated", 0),
                "selected_job_id": state.get("selected_job_id"),
                "matches": state.get("matches", []),
                "scoring_note": (
                    "Match scores are heuristic ranking signals, "
                    "not probabilities of hiring."
                ),
            },
            "resume_optimization": state.get("suggestions", {}),
            "quality_review": state.get("review", {}),
            "errors": state.get("errors", []),
        }
    }


# ---------------------------------------------------------
# BUILD THE LANGGRAPH WORKFLOW
# ---------------------------------------------------------
builder = StateGraph(CareerCopilotState)

builder.add_node("discover_jobs", discover_jobs_node)
builder.add_node("match_jobs", match_jobs_node)
builder.add_node("optimize_resume", optimize_resume_node)
builder.add_node("review_resume", review_resume_node)
builder.add_node("build_report", build_report_node)

builder.add_edge(START, "discover_jobs")
builder.add_edge("discover_jobs", "match_jobs")
builder.add_edge("match_jobs", "optimize_resume")
builder.add_edge("optimize_resume", "review_resume")
builder.add_edge("review_resume", "build_report")
builder.add_edge("build_report", END)

career_copilot_graph = builder.compile()


# ---------------------------------------------------------
# RUN THE COMPLETE WORKFLOW
# ---------------------------------------------------------
async def main():
    # Replace candidate_id with an existing candidate ID in PostgreSQL.
    inputs = {
        "candidate_id": 1,
        "search": "data scientist",
        "category": "",
        "discovery_limit": 10,
        "matching_limit": 10,
        "errors": [],
    }

    print("=" * 65)
    print("AMANAI LAB — AI CAREER COPILOT")
    print("=" * 65)

    result = await career_copilot_graph.ainvoke(inputs)

    report = result.get("report", {})

    print("\n" + "=" * 65)
    print("FINAL CAREER COPILOT REPORT")
    print("=" * 65)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
