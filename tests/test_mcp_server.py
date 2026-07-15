"""
Quick test to verify the Central MCP Server works correctly over stdio.
Run: python tests/test_mcp_server.py
"""
import sys
import io
import asyncio

# Force UTF-8 so Windows cp1252 doesn't crash on special characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Tell the MCP client how to spawn the server process
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.central_server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # 1. Initialize the connection
            await session.initialize()
            print("Connected to MCP Server!")

            # 2. List all available tools
            tools_result = await session.list_tools()
            print(f"\nAvailable Tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"   - {tool.name}: {tool.description}")

            # 3. Actually CALL the read_resume tool
            print("\n📄 Calling read_resume tool...")
            resume_result = await session.call_tool("read_resume", arguments={})
            print("\n--- Resume Content ---")
            print(resume_result.content[0].text[:400] + "...\n[TRUNCATED]")
            print("--- End ---")

            # 4. CALL the new search_web tool
            print("\n🌐 Calling search_web tool...")
            search_args = {"query": "Top AI Engineering news today", "max_results": 3}
            search_result = await session.call_tool("search_web", arguments=search_args)
            print("\n--- Web Search Results ---")
            print(search_result.content[0].text)
            print("--- End ---")

if __name__ == "__main__":
    asyncio.run(main())
