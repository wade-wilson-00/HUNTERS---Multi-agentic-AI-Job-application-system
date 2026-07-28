"""
mcp_server/tools/memory_tool.py
MCP tool to search long-term semantic memory stored in Chroma DB.
"""

from mcp_server.mcp import mcp
from context.memory_store import memory_store

@mcp.tool()
def search_past_memories(query: str) -> str:
    """
    Searches Hunter's long-term semantic memory for past conversations, 
    user preferences, previous topics, or stored job search history.
    
    Args:
        query: The search query (e.g. 'what job preferences did the user mention?', 'past discussion about cover letter')
    """
    return memory_store.search_memories(query=query, n_results=4)
