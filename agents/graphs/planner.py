from langchain_core.messages import SystemMessage
from agents.graphs.hunter_state import HunterState
from agents.graphs.groq_llm import chat_llm
from context.context_builder import HUNTER_FULL_CONTEXT

HISTORY_WINDOW = 6        # rolling message cap — keeps tokens under Groq's 6k TPM limit
MAX_CONTENT_CHARS = 1500  # truncation cap for oversized tool outputs (e.g. web search dumps)


def make_planner_node(tools: list):
    """
    Factory that returns a planner_node coroutine pre-bound to the given tool list.
    Called once in build_hunter_graph() — no MCP subprocess is spawned here.
    """
    llm_with_tools = chat_llm.bind_tools(tools)

    async def planner_node(state: HunterState):
        # ── Sliding window ────────────────────────────────────────────────
        recent_messages = list(state["messages"])[-HISTORY_WINDOW:]

        # ── Truncate oversized tool outputs ───────────────────────────────
        sanitized = []
        for msg in recent_messages:
            if (
                hasattr(msg, "content")
                and isinstance(msg.content, str)
                and len(msg.content) > MAX_CONTENT_CHARS
            ):
                clipped = msg.model_copy()
                clipped.content = msg.content[:MAX_CONTENT_CHARS] + "\n...[truncated for brevity]"
                sanitized.append(clipped)
            else:
                sanitized.append(msg)

        messages_with_context = [SystemMessage(content=HUNTER_FULL_CONTEXT)] + sanitized
        response = await llm_with_tools.ainvoke(messages_with_context)
        return {"messages": [response]}

    return planner_node
