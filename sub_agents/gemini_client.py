import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)

def gemini_llm(json_mode: bool = False, temperature: float = 0.2):
    """
    Wrapper interface compatible with generating content using google.genai SDK.
    """
    client = get_gemini_client()

    class GeminiWrapper:
        def generate_content(self, prompt: str):
            config = types.GenerateContentConfig(
                response_mime_type="application/json" if json_mode else "text/plain",
                temperature=temperature,
                max_output_tokens=4096,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
            return client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=config,
            )

    return GeminiWrapper()
