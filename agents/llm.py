import os
from dotenv import load_dotenv
from huggingface_hub import AsyncInferenceClient

load_dotenv()

api_key = os.getenv("HUGGING_FACE_API")
if not api_key:
    raise EnvironmentError(
        "Missing HUGGING_FACE_API key. "
        "Please add it to your .env file: HUGGING_FACE_API=hf_..."
    )

client = AsyncInferenceClient(api_key=api_key)