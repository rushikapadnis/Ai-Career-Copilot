
import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ---------------------------------------------------------
# MCP Client Configuration
# ---------------------------------------------------------

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_servers.job_discovery_server"],
)


# ---------------------------------------------------------
# MCP Client: Call Job Discovery Server
# ---------------------------------------------------------

async def call_job_discovery_mcp(
    search: str = "",
    category: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    """
    Connect to the Job Discovery MCP server and call search_jobs.

    Returns a dictionary compatible with career_copilot_graph.py.
    """

    try:
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "search_jobs",
                    arguments={
                        "search": search,
                        "category": category,
                        "limit": limit,
                    },
                )

                if result.isError:
                    raise RuntimeError(
                        "Job Discovery MCP tool returned an error."
                    )

                # MCP tools commonly return JSON in a text content block.
                for content in result.content:
                    if getattr(content, "text", None):
                        try:
                            payload = json.loads(content.text)
                        except json.JSONDecodeError:
                            continue

                        if isinstance(payload, dict):
                            return payload

                # Some MCP SDK versions expose structured content.
                structured = getattr(
                    result,
                    "structuredContent",
                    None,
                )

                if isinstance(structured, dict):
                    return structured

                raise RuntimeError(
                    "MCP search_jobs returned no valid JSON result."
                )

    except Exception as exc:
        raise RuntimeError(
            f"Could not call Job Discovery MCP server: {exc}"
        ) from exc


# ---------------------------------------------------------
# Optional Direct Test
# ---------------------------------------------------------

async def main() -> None:
    result = await call_job_discovery_mcp(
        search="data scientist",
        category="",
        limit=10,
    )

    print("Provider:", result.get("provider"))
    print("Count:", result.get("count"))
    print("Note:", result.get("note"))

    for job in result.get("jobs", []):
        print(
            job.get("title"),
            "|",
            job.get("company"),
            "|",
            job.get("job_url"),
        )


if __name__ == "__main__":
    asyncio.run(main())
