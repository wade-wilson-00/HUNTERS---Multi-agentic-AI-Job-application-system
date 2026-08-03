from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# ── Single Hunter LLM ─────────────────────────────────────────────────────────
# One LLM instance for all nodes.
#
# Previously we had planner_llm + summary_llm = 2 API calls per turn.
# This burned ~4,000 tokens/turn on a 6,000 TPM limit — crashing after 1-2 turns.
#
# Now: 1 API call per turn. Summary node is a pure pass-through (no ainvoke).
# The planner outputs voice-ready responses directly via the merged system prompt.
#
# max_tokens=500  → covers a full warm voice response
# temperature=0.7 → balanced: focused enough for tool calling, warm enough for personality
hunter_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=500,
)

# Aliases so any remaining imports don't break
planner_llm = hunter_llm
summary_llm = hunter_llm
