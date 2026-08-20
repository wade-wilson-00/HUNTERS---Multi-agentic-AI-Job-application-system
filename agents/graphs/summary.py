from agents.graphs.hunter_state import HunterState
from langchain_core.messages import HumanMessage, AIMessage
from context.memory_store import memory_store
from langchain_core.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig


async def summary_node(state: HunterState, config: RunnableConfig) -> dict:
    """
    Pass-through node — lightweight, no secondary LLM call.

    Responsibilities:
      1. Extracts the planner's final AI response from state.
      2. Calls smart_upsert_episodic_memory() to consolidate this session's
         episodic summary in ChromaDB via an LLM-powered upsert (one stable
         document per session_id — no overlap).
      3. Caches the resume if read_resume was called for the first time.
      4. Runs Dynamic Pruning (RemoveMessage) to keep SQLite lean.
    """
    prev_ai_message = None
    user_input = ""
    tool_result_content = ""

    for msg in reversed(state["messages"]):
        if not user_input and isinstance(msg, HumanMessage):
            user_input = msg.content if isinstance(msg.content, str) else ""
        if not prev_ai_message and isinstance(msg, AIMessage) and not msg.tool_calls:
            prev_ai_message = msg

    if not prev_ai_message:
        return {"final_response": "I'm sorry, I couldn't complete that task."}

    response_text = prev_ai_message.content

    # ── Cache resume if read_resume was called this turn ─────────────────────
    # If the resume isn't cached yet, scan tool messages from this turn and
    # store the result so the planner never has to call the tool again.
    cached_resume = state.get("cached_resume", "")
    if not cached_resume:
        for msg in state["messages"]:
            if hasattr(msg, "type") and msg.type == "tool":
                content = getattr(msg, "content", "")
                if isinstance(content, str) and content.startswith("[Source:"):
                    tool_result_content = content
                    break

    updates: dict = {"final_response": response_text}
    if tool_result_content:
        updates["cached_resume"] = tool_result_content

    # ── Smart Session-Based Episodic Memory Upsert ───────────────────────────
    # Pull the thread_id (session_id) from LangGraph config so we can maintain
    # one stable episodic document per session in ChromaDB.
    if user_input and response_text:
        try:
            session_id = (
                config.get("configurable", {}).get("thread_id", "default_session")
                if config else "default_session"
            )
            await memory_store.add_episodic_memory(
                session_id=session_id,
                user_input=user_input,
                response_text=response_text,
            )
        except Exception as e:
            print(f"[MemoryStore] Warning: Failed to upsert episodic memory: {e}")

        # ── Gemini Semantic Fact Extraction ──────────────────────────────────
        # Runs after episodic upsert. Non-blocking — failure here never
        # affects Hunter's response. Gemini extracts structured facts
        # (skills, roles, locations, preferences) and deduplicates them.
        try:
            await memory_store.add_semantic_memory(
                user_input=user_input,
                response_text=response_text,
            )
        except Exception as e:
            print(f"[MemoryStore] Warning: Failed to extract semantic facts: {e}")

    #---- Dynamic Pruning and Summarization----
    messages = state.get("messages", [])
    if len(messages) > 6:
        to_prune = messages[:-2]

        prune = [RemoveMessage(id = m.id) for m in to_prune if getattr(m, "id", None)]
        updates["messages"] = prune
    return updates

