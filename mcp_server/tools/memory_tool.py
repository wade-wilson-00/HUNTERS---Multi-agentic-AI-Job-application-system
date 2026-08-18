"""
mcp_server/tools/memory_tool.py
MCP tool to search long-term semantic memory stored in Chroma DB.
"""

from mcp_server.mcp import mcp
from context.memory_store import memory_store

@mcp.tool()
def search_past_memories(query: str, memory_type: str = None) -> str:
    """
    Searches Hunter's long-term memory for past conversations (episodic memory), 
    user preferences, skills, previous topics, or stored job search history (semantic memory).
    Uses Hybrid Search (Dense vector similarity + BM25 keyword matching + RRF reranking).
    
    Args:
        query: The search query (e.g. 'what job preferences did the user mention?', 'past discussion about cover letter')
        memory_type: Optional filter: 'semantic' (facts, skills, preferences) or 'episodic' (conversation session summaries)
    """
    return memory_store.hybrid_search(query=query, n_results=4, memory_type=memory_type)
