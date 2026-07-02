"""
HUNTERS — VAD-based Voice Listener

Always-on microphone listener using Silero VAD for real-time speech detection.
Returns audio as a numpy buffer directly — no file saving, no manual triggers.

Flow:
  Mic (continuous) → Silero VAD (32ms chunks) → detect speech end → return numpy buffer
"""

import numpy as np
import pyaudio
import asyncio
import sys

from config.settings import (
    VAD_SAMPLE_RATE,
    VAD_CHUNK_MS,
    VAD_CHUNK_SIZE,
    VAD_SILENCE_MS,
    VAD_THRESHOLD,
    VAD_MIN_SPEECH_MS,
)


class VADListener:
    """
    Hands-free, always-on microphone listener.
    Uses Silero VAD to detect when the user starts and stops speaking,
    then returns the captured audio as a numpy float32 array (16kHz, mono).
    """

    def __init__(self):
        print("Loading Silero VAD model...")
        # Import here to allow graceful fallback if silero not installed
        import torch
        self.torch = torch
        
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True,
        )
        self.vad_model = model
        self.vad_model.eval()
        torch.set_num_threads(1)  # VAD is lightweight, single thread is fine

        # PyAudio setup
        self.pa = pyaudio.PyAudio()
        self.stream = None

        # State
        self._is_listening = False

        print("VAD Listener ready.")

    def _open_mic_stream(self):
        """Opens the microphone input stream."""
        if self.stream is not None and self.stream.is_active():
            return
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=VAD_SAMPLE_RATE,
            input=True,
            frames_per_buffer=VAD_CHUNK_SIZE,
        )

    def _close_mic_stream(self):
        """Closes the microphone stream."""
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def _read_chunk(self) -> np.ndarray:
        """
        Read a single chunk from the microphone.
        Returns float32 numpy array normalized to [-1.0, 1.0].
        """
        raw = self.stream.read(VAD_CHUNK_SIZE, exception_on_overflow=False)
        audio_int16 = np.frombuffer(raw, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return audio_float32

    def _get_speech_prob(self, audio_chunk: np.ndarray) -> float:
        """Run Silero VAD on a single chunk, return speech probability."""
        tensor = self.torch.from_numpy(audio_chunk)
        prob = self.vad_model(tensor, VAD_SAMPLE_RATE).item()
        return prob

    async def listen(self) -> np.ndarray:
        """
        Listen for speech using VAD. Returns when the user finishes speaking.
        
        Returns:
            np.ndarray: float32 audio buffer (16kHz, mono, [-1.0, 1.0])
                        Ready to pass directly to Whisper.
        """
        self._open_mic_stream()
        self._is_listening = True

        loop = asyncio.get_event_loop()

        audio_buffer = []
        is_speaking = False
        silence_chunks = 0
        speech_chunks = 0

        # How many silent chunks = end of speech
        chunks_per_second = 1000 / VAD_CHUNK_MS
        silence_chunks_needed = int(VAD_SILENCE_MS / VAD_CHUNK_MS)
        min_speech_chunks = int(VAD_MIN_SPEECH_MS / VAD_CHUNK_MS)

        try:
            while self._is_listening:
                # Read mic in executor to avoid blocking the event loop
                chunk = await loop.run_in_executor(None, self._read_chunk)
                prob = self._get_speech_prob(chunk)

                if prob >= VAD_THRESHOLD:
                    # Speech detected
                    if not is_speaking:
                        is_speaking = True
                        silence_chunks = 0
                        speech_chunks = 0
                    
                    speech_chunks += 1
                    silence_chunks = 0
                    audio_buffer.append(chunk)

                elif is_speaking:
                    # We were speaking, now silence
                    silence_chunks += 1
                    audio_buffer.append(chunk)  # Keep some trailing silence

                    if silence_chunks >= silence_chunks_needed:
                        # Speech ended — check minimum duration
                        if speech_chunks >= min_speech_chunks:
                            break
                        else:
                            # Too short, likely a false trigger — reset
                            audio_buffer.clear()
                            is_speaking = False
                            silence_chunks = 0
                            speech_chunks = 0

                # Small yield to keep event loop responsive
                await asyncio.sleep(0)

        except Exception as e:
            print(f"VAD Listener error: {e}")

        if not audio_buffer:
            return np.array([], dtype=np.float32)

        # Concatenate all chunks into a single buffer
        full_audio = np.concatenate(audio_buffer)
        return full_audio

    def stop(self):
        """Stop listening."""
        self._is_listening = False
        self._close_mic_stream()

    def cleanup(self):
        """Clean up PyAudio resources."""
        self.stop()
        self.pa.terminate()


# ─── Test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        vad = VADListener()
        print("\nSpeak something (VAD will detect when you stop)...")
        audio = await vad.listen()
        print(f"Captured {len(audio)} samples ({len(audio)/VAD_SAMPLE_RATE:.1f}s)")
        vad.cleanup()

    asyncio.run(test())
