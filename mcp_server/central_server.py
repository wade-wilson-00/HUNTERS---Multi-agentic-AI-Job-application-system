from mcp_server.mcp import mcp
# ── Register Tool Modules ─────────────────────────────────────────────────
# Add an import here for every new tool file you create.
# The import itself is what registers the tools — no other wiring needed.

from mcp_server.tools import resume_read  
from mcp_server.tools import web_search

if __name__ == "__main__":
    mcp.run(transport='stdio')
