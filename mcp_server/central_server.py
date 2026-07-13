
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Hunters Central MCP Server")

# ── Register Tool Modules ─────────────────────────────────────────────────
# Add an import here for every new tool file you create.
# The import itself is what registers the tools — no other wiring needed.

from mcp_server.tools import resume_read  

if __name__ == "__main__":
    mcp.run(transport='stdio')
