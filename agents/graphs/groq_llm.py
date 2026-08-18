from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# ── Single Hunter LLM ─────────────────────────────────────────────────────────
# One LLM instance shared across all graph nodes (planner, summary, memory).
#
# Model: qwen/qwen3.6-27b (Groq-hosted)
# Switched from deprecated llama-3.1-8b-instant. Qwen 3.6 27B provides
# significantly stronger multi-step reasoning and instruction following,
# which improves tool selection, episodic summarization, and response quality.
#
# max_tokens=800  → sufficient for rich voice responses + tool call payloads
# temperature=0.7 → balanced: focused for tool calling, warm for personality
hunter_llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=800,
)

# Aliases so any remaining imports don't break
planner_llm = hunter_llm
summary_llm = hunter_llm

