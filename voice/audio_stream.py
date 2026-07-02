"""
HUNTERS — Async Audio Output Manager

Queue-based speaker playback using PyAudio.
Receives audio chunks (PCM16) via an asyncio.Queue and plays them seamlessly.
Supports clearing the buffer for interrupt/barge-in.
"""

import asyncio
import pyaudio
import numpy as np

from config.settings import SPEAKER_SAMPLE_RATE, SPEAKER_CHANNELS, SPEAKER_SAMPLE_WIDTH


class SpeakerStream:
    """
    Async audio output stream.
    TTS modules push PCM audio bytes into the queue, 
    the consumer task writes them to the speaker.
    """

    def __init__(self, sample_rate: int = SPEAKER_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.queue = asyncio.Queue()
        self._running = False
        self._playing = False

    def _open_output_stream(self):
        """Open the PyAudio output stream."""
        if self.stream is not None and self.stream.is_active():
            return
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=SPEAKER_CHANNELS,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=1024,
        )

    def _close_output_stream(self):
        """Close the PyAudio output stream."""
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    async def start(self):
        """Start the playback consumer loop."""
        self._open_output_stream()
        self._running = True

    async def play(self, audio_bytes: bytes):
        """Add audio bytes (PCM16) to the playback queue."""
        await self.queue.put(audio_bytes)

    async def play_all(self):
        """
        Consume and play all queued audio chunks.
        Blocks until the queue is empty and a sentinel (None) is received.
        """
        loop = asyncio.get_event_loop()
        self._playing = True

        while self._running:
            try:
                chunk = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            if chunk is None:
                # Sentinel — done playing this response
                break

            # Write to speaker in executor to avoid blocking
            await loop.run_in_executor(None, self.stream.write, chunk)

        self._playing = False

    async def drain(self):
        """Play all remaining audio in the queue, then return."""
        # Send sentinel to signal end
        await self.queue.put(None)
        await self.play_all()

    def clear(self):
        """Clear the playback queue (for interrupt/barge-in support)."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    @property
    def is_playing(self) -> bool:
        return self._playing

    def cleanup(self):
        """Clean up PyAudio resources."""
        self._running = False
        self.clear()
        self._close_output_stream()
        self.pa.terminate()


# ─── Test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import struct
    import math

    async def test():
        speaker = SpeakerStream(sample_rate=24000)
        await speaker.start()

        # Generate a simple sine wave test tone (440Hz, 1 second)
        duration = 1.0
        freq = 440
        n_samples = int(24000 * duration)
        for i in range(0, n_samples, 1024):
            chunk_samples = min(1024, n_samples - i)
            pcm = b""
            for j in range(chunk_samples):
                sample = int(16000 * math.sin(2 * math.pi * freq * (i + j) / 24000))
                pcm += struct.pack('<h', sample)
            await speaker.play(pcm)

        await speaker.drain()
        speaker.cleanup()
        print("Speaker test complete.")

    asyncio.run(test())
