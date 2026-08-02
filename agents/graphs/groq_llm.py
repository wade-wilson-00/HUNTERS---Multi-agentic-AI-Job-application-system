from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# ── Planner LLM ───────────────────────────────────────────────────────────────
# Used by the Planner node for ReAct reasoning and tool selection.
# max_tokens is capped to keep each request well under Groq's 6,000 TPM limit.
# Personality and warmth are NOT needed here — that's the summary node's job.
planner_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
    max_tokens=350,
)

# ── Summary LLM ───────────────────────────────────────────────────────────────
# Used by the Summary node to transform planner output into Hunter's voice.
# No token cap — Hunter can be as warm, funny, and expressive as the moment calls for.
summary_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.8,
    max_tokens=600,
)
