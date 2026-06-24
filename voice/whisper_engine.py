import os
import speech_recognition as sr

class WhisperEngine:
    def __init__(self, model_size="base.en", device="cpu", compute_type="int8"):
        # We are using Google Speech Recognition as a fallback because 
        # faster-whisper installation is blocked by Windows Defender.
        print("Initializing Speech-to-Text (Google Fallback Mode)...")
        self.recognizer = sr.Recognizer()
        print("Speech-to-Text ready.")

    def transcribe(self, audio_path: str) -> str:
        """Transcribes the audio file and returns the text using Google's API."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                
            # Use Google's free API
            text = self.recognizer.recognize_google(audio_data)
            return text.strip()
        except sr.UnknownValueError:
            return "" # Could not understand the audio
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

# Simple test if run directly
if __name__ == "__main__":
    engine = WhisperEngine()
    print("Ready to transcribe.")
