import os
import httpx
from config.settings import VAD_SAMPLE_RATE

class SarvamSTT:
    def __init__(self):
        self.api_key = os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Missing SARVAM_API_KEY in .env file.")
        
        self.endpoint = "https://api.sarvam.ai/speech-to-text"
        self.model = "saaras:v3"

    async def transcribe(self, wav_bytes: bytes) -> str:
        """
        Send WAV bytes to Sarvam AI STT API and return the transcribed text.
        """
        files = {
            'file': ('audio.wav', wav_bytes, 'audio/wav')
        }
        data = {
            'model': self.model,
            'prompt': '', # Optional prompt
        }
        
        headers = {
            'api-subscription-key': self.api_key
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    data=data,
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                return result.get('transcript', '')
            except Exception as e:
                print(f"[Sarvam STT] Error transcribing audio: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"[Sarvam STT] Response: {e.response.text}")
                return ""
