from agents.graphs.hunter_state import HunterState
from langchain_core.messages import HumanMessage, AIMessage
from context.memory_store import memory_store
from langchain_core.messages import RemoveMessage


async def summary_node(state: HunterState) -> dict:
    """
    Pass-through node — NO LLM call here.

    Previously this called summary_llm.ainvoke() to rewrite the planner output
    into Hunter's voice. That was the second of two API calls per turn, which
    alone burned ~1,500 tokens and routinely caused 6k TPM 429 errors.

    Now: the planner already outputs in Hunter's voice (personality merged into
    the system prompt). This node just:
      1. Extracts the planner's final response from state.
      2. Writes the turn to ChromaDB for long-term memory.
      3. Returns final_response to the graph.

    If the resume was loaded for the first time this turn, it also caches it.
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

    # ── Auto-index turn to long-term episodic memory (ChromaDB) ──────────────
    if user_input and response_text:
        try:
            summary_entry = f"User inquired: {user_input.strip()}\nHunter responded: {response_text.strip()}"
            memory_store.add_episodic_memory(
                summary_text=summary_entry,
                metadata={
                    "user_input": user_input[:200],
                    "assistant_response": response_text[:200]
                }
            )
        except Exception as e:
            print(f"[MemoryStore] Warning: Failed to auto-index turn: {e}")
    
    #---- Dynamic Pruning and Summarization----
    messages = state.get("messages", [])
    if len(messages) > 6:
        to_prune = messages[:-2]

        prune = [RemoveMessage(id = m.id) for m in to_prune if getattr(m, "id", None)]
        updates["messages"] = prune
    return updates
