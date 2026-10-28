
import re
import sys
import time
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP


# --------------------------------------------------
# Configuration
# --------------------------------------------------

mcp = FastMCP("job-discovery")

JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
MAX_LIMIT = 20

DATA_ROLE_PATTERNS = [
    r"\bdata scientist\b",
    r"\bdata science\b",
    r"\bmachine learning\b",
    r"\bapplied scientist\b",
    r"\bresearch scientist\b",
    r"\bai scientist\b",
    r"\bartificial intelligence scientist\b",
    r"\bml engineer\b",
    r"\bmlops\b",
]

DATA_ROLE_SEARCH_TERMS = [
    "data scientist",
    "machine learning",
    "applied scientist",
    "data science",
]


# --------------------------------------------------
# HTTP Client
# --------------------------------------------------

def _get_json(
    params: dict[str, Any] | None = None,
) -> dict:
    """Fetch current remote job listings from Jobicy."""

    headers = {
        "Accept": "application/json",
        "User-Agent": "AmanAI-Career-Copilot/1.0",
    }

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                JOBICY_URL,
                params=params or {},
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )

            print(
                f"[job-provider] GET {response.url} "
                f"-> HTTP {response.status_code}",
                file=sys.stderr,
                flush=True,
            )

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise RuntimeError(
                    "Jobicy returned an unexpected response format."
                )

            if data.get("success") is False:
                raise RuntimeError(
                    f"Jobicy reported an unsuccessful request: "
                    f"{data.get('friendlyNotice', 'Unknown error')}"
                )

            return data

        except requests.exceptions.HTTPError as exc:
            status = (
                exc.response.status_code
                if exc.response is not None
                else 0
            )

            if status not in {429, 500, 502, 503, 504}:
                raise RuntimeError(
                    f"Jobicy returned HTTP {status}: {exc}"
                ) from exc

            last_error = exc

        except requests.exceptions.RequestException as exc:
            last_error = exc

        except ValueError as exc:
            raise RuntimeError(
                "Jobicy returned invalid JSON."
            ) from exc

        if attempt < MAX_RETRIES - 1:
            delay = 2 ** attempt

            print(
                f"[job-provider] Retrying in {delay}s: {last_error}",
                file=sys.stderr,
                flush=True,
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Jobicy request failed after {MAX_RETRIES} attempts: "
        f"{last_error}"
    ) from last_error


# --------------------------------------------------
# Job Normalization
# --------------------------------------------------

def _normalize_job(item: dict) -> dict:
    """Convert Jobicy fields to the existing application format."""

    if not isinstance(item, dict):
        raise RuntimeError("Jobicy returned an invalid job record.")

    job_id = (
        item.get("id")
        or item.get("jobId")
        or item.get("job_id")
        or item.get("url")
        or item.get("jobUrl")
        or ""
    )

    title = item.get("jobTitle") or item.get("title")
    company = item.get("companyName") or item.get("company")
    location = (
        item.get("jobGeo")
        or item.get("jobLocation")
        or item.get("location")
    )

    description = (
        item.get("jobDescription")
        or item.get("jobExcerpt")
        or item.get("description")
        or ""
    )

    job_url = (
        item.get("url")
        or item.get("jobUrl")
        or item.get("job_url")
    )

    industry = item.get("jobIndustry") or item.get("industry") or []
    if isinstance(industry, list):
        category = ", ".join(str(value) for value in industry)
    else:
        category = str(industry or "")

    return {
        "external_id": str(job_id),
        "title": title,
        "company": company,
        "location": location,
        "category": category,
        "job_type": item.get("jobType") or item.get("job_type"),
        "description": description,
        "publication_date": (
            item.get("pubDate")
            or item.get("publicationDate")
            or item.get("publication_date")
        ),
        "job_url": job_url,
        "source": "Jobicy",
    }


# --------------------------------------------------
# Relevance Helpers
# --------------------------------------------------

def _is_data_role_search(search: str) -> bool:
    normalized = search.lower().strip()

    return any(
        re.search(pattern, normalized)
        for pattern in DATA_ROLE_PATTERNS
    )


def _title_score(title: str, search: str) -> int:
    """Prioritize job titles relevant to the requested role."""

    title = (title or "").lower()
    search = (search or "").lower()

    if re.search(r"\bdata scientist\b", title):
        score = 100
    elif re.search(r"\bdata science\b", title):
        score = 95
    elif re.search(r"\bapplied scientist\b", title):
        score = 92
    elif re.search(r"\bmachine learning\b", title):
        score = 88
    elif re.search(r"\bml engineer\b", title):
        score = 85
    elif re.search(r"\bresearch scientist\b", title):
        score = 80
    elif re.search(r"\bai scientist\b", title):
        score = 80
    elif re.search(r"\bmlops\b", title):
        score = 75
    else:
        score = 0

    if "senior" in title or "lead" in title or "staff" in title:
        score += 2

    if "data scientist" in search and "data scientist" in title:
        score += 10

    return score


def _is_relevant_data_role(job: dict) -> bool:
    title = job.get("title") or ""

    return any(
        re.search(pattern, title.lower())
        for pattern in DATA_ROLE_PATTERNS
    )


def _fetch_jobs(
    search: str = "",
    category: str = "",
    count: int = 50,
) -> list[dict]:
    """Fetch and normalize Jobicy results."""

    params: dict[str, Any] = {
        "count": max(1, min(count, 50)),
    }

    if search.strip():
        params["tag"] = search.strip()

    # Apply the category filter for Data Science-oriented searches.
    if category.strip():
        params["industry"] = category.strip()
    elif _is_data_role_search(search):
        params["industry"] = "data-science"

    data = _get_json(params)
    raw_jobs = data.get("jobs", [])

    if not isinstance(raw_jobs, list):
        raise RuntimeError("Jobicy returned an invalid jobs list.")

    jobs = []

    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

        job = _normalize_job(item)

        # Ignore records without a title or usable URL.
        if not job["title"] or not job["job_url"]:
            continue

        jobs.append(job)

    return jobs


# --------------------------------------------------
# MCP Tool 1: Search Jobs
# --------------------------------------------------

@mcp.tool()
def search_jobs(
    search: str = "",
    category: str = "",
    limit: int = 10,
) -> dict:
    """
    Search remote jobs using Jobicy.

    Args:
        search: Target role or keyword, e.g. data scientist.
        category: Optional Jobicy industry filter.
        limit: Maximum number of results, from 1 to 20.

    Returns:
        Normalized job listings and provider metadata.
    """

    limit = max(1, min(int(limit), MAX_LIMIT))
    search = search.strip()
    category = category.strip()

    is_data_role = _is_data_role_search(search)

    if is_data_role:
        # Search related terms, then deduplicate and rank results.
        collected: dict[str, dict] = {}
        queries_used = []

        for query in DATA_ROLE_SEARCH_TERMS:
            try:
                results = _fetch_jobs(
                    search=query,
                    category=category,
                    count=50,
                )

                queries_used.append(query)

                for job in results:
                    key = job.get("external_id") or job.get("job_url")
                    if key:
                        collected[key] = job

            except Exception as exc:
                print(
                    f"[job-provider] Search failed for "
                    f"{query!r}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )

        jobs = list(collected.values())

        # Strict title relevance: shared skills alone are insufficient.
        jobs = [
            job for job in jobs
            if _is_relevant_data_role(job)
        ]

        jobs.sort(
            key=lambda job: _title_score(
                job.get("title", ""),
                search,
            ),
            reverse=True,
        )

    else:
        jobs = _fetch_jobs(
            search=search,
            category=category,
            count=50,
        )

        queries_used = [search] if search else []

        # Deduplicate results while preserving the first occurrence.
        unique = {}

        for job in jobs:
            key = job.get("external_id") or job.get("job_url")
            if key:
                unique[key] = job

        jobs = list(unique.values())

    selected = jobs[:limit]

    if not selected:
        note = (
            "No matching job listings were found in the current "
            "Jobicy results. Try a related role or check again later."
        )
    else:
        note = (
            "Listings retrieved from Jobicy. Check each listing's "
            "location, seniority, eligibility and application page "
            "before applying."
        )

    return {
        "provider": "Jobicy",
        "search": search,
        "category": category,
        "count": len(selected),
        "jobs": selected,
        "queries_used": queries_used,
        "note": note,
    }


# --------------------------------------------------
# MCP Tool 2: Get Job Details
# --------------------------------------------------

@mcp.tool()
def get_job_details(job_id: str) -> dict:
    """
    Find a job in the current Jobicy results.

    Args:
        job_id: The external_id returned by search_jobs.
    """

    if not job_id or not job_id.strip():
        return {"error": "job_id is required."}

    job_id = job_id.strip()

    # Search the provider's current listings; do not invent a
    # single-job endpoint that has not been verified.
    data = _get_json({"count": 50})
    raw_jobs = data.get("jobs", [])

    if not isinstance(raw_jobs, list):
        raise RuntimeError("Jobicy returned an invalid jobs list.")

    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

        job = _normalize_job(item)

        if job["external_id"] == job_id:
            return {
                "provider": "Jobicy",
                "job": job,
            }

    return {
        "provider": "Jobicy",
        "error": (
            f"Job {job_id} was not found in the current response. "
            "It may no longer be available."
        ),
    }


# --------------------------------------------------
# Start MCP Server
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
