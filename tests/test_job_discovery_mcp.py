
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.job_discovery_server"],
        stderr="inherit",
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("\n--- LIVE JOB DISCOVERY MCP TOOLS ---")
            for tool in tools.tools:
                print(f"- {tool.name}")

            print("\n--- CALLING EXTERNAL JOB API ---")
            result = await session.call_tool(
                "search_jobs",
                arguments={
                    "search": "data scientist",
                    "limit": 5,
                },
            )

            if result.isError:
                print("\n--- MCP TOOL ERROR DETAILS ---")
                for item in result.content:
                    if hasattr(item, "text"):
                        print(item.text)
                return

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
