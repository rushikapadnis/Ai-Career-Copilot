
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.career_workspace_server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.list_tools()

            print("\n--- DISCOVERED MCP TOOLS ---")
            for tool in response.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\n--- TEST list_jobs ---")
            result = await session.call_tool(
                "list_jobs",
                {"limit": 5},
            )

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if result.isError:
                raise RuntimeError("MCP list_jobs tool returned an error.")


if __name__ == "__main__":
    asyncio.run(main())
