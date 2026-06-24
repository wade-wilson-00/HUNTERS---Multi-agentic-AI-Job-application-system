import pyttsx3
import re

class TTSEngine:
    def __init__(self):
        # We handle engine initialization inside speak() to prevent 
        # the common pyttsx3 "runAndWait" loop bug on Windows.
        pass

    def speak(self, text: str):
        """Speaks the text synchronously."""
        if not text:
            return
            
        # Clean text of any rogue emojis or special characters that can crash the TTS
        clean_text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
        
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # Try to use a male voice if available (e.g. David on Windows)
            for voice in voices:
                if "David" in voice.name or "male" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 170) # slightly slower for better clarity
            
            engine.say(clean_text)
            engine.runAndWait()
            engine.stop() # Reset the event loop for the next time
            
        except Exception as e:
            print(f"TTS Error: {e}")

# Simple test
if __name__ == "__main__":
    tts = TTSEngine()
    tts.speak("System initialized. I am ready.")
