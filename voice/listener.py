import speech_recognition as sr
import os
import wave
import time

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise initially
        with self.microphone as source:
            print("Adjusting for ambient noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Ready to listen.")

    def listen_and_save(self, output_filename="temp_audio.wav") -> str:
        """Listens to the microphone and saves the audio to a wav file."""
        with self.microphone as source:
            print("\nListening...")
            try:
                # Listen for speech. Timeout if nothing is said after 5 seconds
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("Processing audio...")
                
                # Save the audio data to a file
                with open(output_filename, "wb") as f:
                    f.write(audio.get_wav_data())
                    
                return output_filename
            except sr.WaitTimeoutError:
                print("No speech detected.")
                return None
            except Exception as e:
                print(f"Error during listening: {e}")
                return None

if __name__ == "__main__":
    listener = Listener()
    filename = listener.listen_and_save()
    if filename:
        print(f"Saved to {filename}")
