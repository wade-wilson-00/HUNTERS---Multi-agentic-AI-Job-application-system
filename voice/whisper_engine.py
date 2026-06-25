import os
from faster_whisper import WhisperModel

class WhisperEngine:
    def __init__(self, model_size="small.en", device="cpu", compute_type="int8"):
       
        print(f"Loading Whisper model '{model_size}' (this may take a moment on first run)...")
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type
        )
        print("Whisper STT engine ready.")

    def transcribe(self, audio_path: str) -> str:
        """Transcribes the audio file and returns the text using local Whisper."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        try:
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=5,
                language="en",
                vad_filter=True,  # Filters out silence for cleaner results
            )
            
            # Combine all segments into a single string
            full_text = " ".join(segment.text.strip() for segment in segments)
            return full_text.strip()
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return ""

# Simple test if run directly
if __name__ == "__main__":
    engine = WhisperEngine()
    print("Whisper is ready to transcribe.")
