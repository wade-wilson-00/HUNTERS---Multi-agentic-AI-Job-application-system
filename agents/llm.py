import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError(
        "Missing GROQ_API_KEY. "
        "Please add it to your .env file: GROQ_API_KEY=gsk_..."
    )

client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)