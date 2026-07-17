from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# LangChain-compatible LLM — used by LangGraph nodes for ReAct reasoning.
# (Different from agents/llm.py which is used for raw SSE streaming in 
# voice mode.)

chat_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
)
