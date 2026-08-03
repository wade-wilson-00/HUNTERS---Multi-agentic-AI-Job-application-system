from langchain_core.messages import SystemMessage
from agents.graphs.hunter_state import HunterState
from agents.graphs.groq_llm import hunter_llm
from context.context_builder import HUNTER_FULL_CONTEXT

HISTORY_WINDOW = 5        # Must cover a full tool-call sequence (Human -> AI[Tool] -> Tool -> AI)
MAX_CONTENT_CHARS = 800   # Truncation cap for oversized tool outputs (web search dumps, etc.)


def make_planner_node(tools: list):
    """
    Factory that returns a planner_node coroutine pre-bound to the given tool list.
    Called once in build_hunter_graph() — no MCP subprocess is spawned here.

    Key optimisations vs. original design:
    - Uses a single hunter_llm (not separate planner + summary LLMs) → 1 API call/turn
    - Injects cached_resume from state into the system prompt so read_resume is
      never called more than once per session
    """
    llm_with_tools = hunter_llm.bind_tools(tools)

    async def planner_node(state: HunterState):
        # ── Build system prompt (optionally with cached resume) ───────────────
        cached_resume = state.get("cached_resume", "")
        if cached_resume:
            system_content = (
                HUNTER_FULL_CONTEXT
                + "\n\n=== USER RESUME (already loaded — do NOT call read_resume again) ===\n"
                + cached_resume[:1200]   # Hard cap: ~300 tokens even if resume is huge
            )
        else:
            system_content = HUNTER_FULL_CONTEXT

        # ── Sliding window ────────────────────────────────────────────────────
        recent_messages = list(state["messages"])[-HISTORY_WINDOW:]

        # ── Truncate oversized tool outputs ───────────────────────────────────
        sanitized = []
        for msg in recent_messages:
            if not hasattr(msg, "content"):
                sanitized.append(msg)
                continue
                
            raw_text = msg.content
            if isinstance(raw_text, list):
                # Extract text blocks if content is a list of dicts (e.g., from ChromaDB)
                raw_text = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in raw_text
                )
            
            if isinstance(raw_text, str) and len(raw_text) > MAX_CONTENT_CHARS:
                clipped = msg.model_copy()
                clipped.content = raw_text[:MAX_CONTENT_CHARS] + "\n...[truncated for brevity]"
                sanitized.append(clipped)
            else:
                sanitized.append(msg)

        messages_with_context = [SystemMessage(content=system_content)] + sanitized
        response = await llm_with_tools.ainvoke(messages_with_context)
        return {"messages": [response]}

    return planner_node
