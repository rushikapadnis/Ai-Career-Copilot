
import pytest

import agents.career_copilot_graph as copilot


class FakeDBSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


@pytest.mark.asyncio
async def test_complete_career_copilot_workflow(monkeypatch):
    # Simulate the MCP job discovery response.
    async def fake_discovery(**kwargs):
        return {
            "jobs": [
                {
                    "external_id": "test-101",
                    "title": "Data Scientist",
                    "company": "Example Company",
                    "location": "Remote",
                    "source": "Test Provider",
                    "job_url": "https://example.com/jobs/101",
                }
            ]
        }

    monkeypatch.setattr(
        copilot,
        "call_job_discovery_mcp",
        fake_discovery,
    )

    # Simulate database persistence.
    monkeypatch.setattr(
        copilot,
        "SessionLocal",
        FakeDBSession,
    )

    monkeypatch.setattr(
        copilot,
        "save_discovered_jobs",
        lambda db, jobs: {
            "inserted": len(jobs),
            "updated": 0,
            "total_processed": len(jobs),
        },
    )

    # Simulate job matching.
    monkeypatch.setattr(
        copilot,
        "run_job_matching",
        lambda candidate_id, limit: {
            "candidate_id": candidate_id,
            "jobs_evaluated": 1,
            "matches": [
                {
                    "job_id": 101,
                    "title": "Data Scientist",
                    "company": "Example Company",
                    "match_score": 80.0,
                    "matched_skills": ["Python"],
                    "missing_skills": ["Docker"],
                    "job_url": "https://example.com/jobs/101",
                }
            ],
            "error": "",
        },
    )

    # Simulate resume optimization.
    monkeypatch.setattr(
        copilot,
        "run_resume_optimization",
        lambda candidate_id, job_id: {
            "suggestions": {
                "job_target": "Data Scientist",
                "supported_matching_skills": ["Python"],
                "improvement_suggestions": [
                    "Add relevant project details supported by evidence."
                ],
            },
            "error": "",
        },
    )

    # Simulate the quality review.
    monkeypatch.setattr(
        copilot,
        "run_quality_review",
        lambda suggestions: {
            "review": {
                "status": "NEEDS_REVIEW",
                "quality_score": 85,
                "human_verification_required": True,
                "issues": [],
            },
            "error": "",
        },
    )

    result = await copilot.career_copilot_graph.ainvoke(
        {
            "candidate_id": 1,
            "search": "data scientist",
            "category": "",
            "discovery_limit": 5,
            "matching_limit": 10,
            "errors": [],
        }
    )

    report = result["report"]

    assert report["candidate_id"] == 1
    assert report["discovery"]["jobs_discovered"] == 1
    assert report["discovery"]["persistence"]["inserted"] == 1

    assert report["job_matching"]["selected_job_id"] == 101
    assert report["job_matching"]["matches"][0]["match_score"] == 80.0

    assert report["resume_optimization"]["job_target"] == "Data Scientist"
    assert report["quality_review"]["status"] == "NEEDS_REVIEW"

    print("PASS: Discovery and persistence data reached the report.")
    print("PASS: Job matching selected the expected job.")
    print("PASS: Resume optimization received the selected job.")
    print("PASS: Quality review was included in the final report.")
    print("PASS: Complete LangGraph workflow test succeeded.")


@pytest.mark.asyncio
async def test_no_positive_job_match_skips_optimization(monkeypatch):
    async def fake_discovery(**kwargs):
        return {"jobs": []}

    monkeypatch.setattr(
        copilot,
        "call_job_discovery_mcp",
        fake_discovery,
    )

    monkeypatch.setattr(copilot, "SessionLocal", FakeDBSession)
    monkeypatch.setattr(
        copilot,
        "save_discovered_jobs",
        lambda db, jobs: {
            "inserted": 0,
            "updated": 0,
            "total_processed": 0,
        },
    )

    monkeypatch.setattr(
        copilot,
        "run_job_matching",
        lambda candidate_id, limit: {
            "candidate_id": candidate_id,
            "jobs_evaluated": 1,
            "matches": [
                {
                    "job_id": 101,
                    "match_score": 0.0,
                }
            ],
            "error": "",
        },
    )

    def unexpected_optimization(**kwargs):
        pytest.fail("Optimization must be skipped when no positive match exists.")

    monkeypatch.setattr(
        copilot,
        "run_resume_optimization",
        unexpected_optimization,
    )

    result = await copilot.career_copilot_graph.ainvoke(
        {
            "candidate_id": 1,
            "search": "data scientist",
            "category": "",
            "discovery_limit": 5,
            "matching_limit": 10,
            "errors": [],
        }
    )

    report = result["report"]

    assert report["job_matching"]["selected_job_id"] is None
    assert report["resume_optimization"] == {}
    assert any(
        "optimization was skipped" in error.lower()
        for error in report["errors"]
    )
