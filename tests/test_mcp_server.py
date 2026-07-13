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
        command="python",
        args=["mcp_servers/central_server.py"],
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
            print("\nCalling read_resume tool...")
            result = await session.call_tool("read_resume", arguments={})
            print("\n--- Resume Content ---")
            print(result.content[0].text[:800] + "...")  # Print first 800 chars
            print("--- End ---")

if __name__ == "__main__":
    asyncio.run(main())
