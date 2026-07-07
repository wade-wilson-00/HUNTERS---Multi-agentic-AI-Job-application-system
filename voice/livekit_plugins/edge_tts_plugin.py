"""
HUNTERS — LiveKit Custom TTS Plugin (Edge TTS)

Wraps Microsoft Edge TTS to implement livekit.agents.tts.TTS interface.
Generates audio frames from text and streams them over the WebRTC track.
"""

import asyncio
import io
from dataclasses import dataclass

import edge_tts
import miniaudio
from livekit.agents import tts, utils
from livekit.agents.tts import SynthesizedAudio, SynthesisEventType

from config.settings import EDGE_TTS_VOICE, EDGE_TTS_RATE, EDGE_TTS_VOLUME, SPEAKER_SAMPLE_RATE

# LiveKit expects 48kHz for WebRTC output
LIVEKIT_SAMPLE_RATE = 48000
LIVEKIT_CHANNELS = 1


class EdgeTTS(tts.TTS):
    """
    LiveKit TTS plugin wrapping Microsoft Edge TTS (free, neural voices).
    Synthesizes speech from text and streams PCM audio frames to the WebRTC track.
    """

    def __init__(self):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=LIVEKIT_SAMPLE_RATE,
            num_channels=LIVEKIT_CHANNELS,
        )
        self.voice = EDGE_TTS_VOICE
        self.rate = EDGE_TTS_RATE
        self.volume = EDGE_TTS_VOLUME

    def synthesize(self, text: str, *, conn_options=None) -> "EdgeTTSStream":
        return EdgeTTSStream(self, text)


class EdgeTTSStream(tts.SynthesizeStream):
    """Handles the actual async synthesis and yields AudioFrames."""

    def __init__(self, tts_instance: EdgeTTS, text: str):
        super().__init__(tts_instance)
        self._text = text
        self._tts = tts_instance

    async def _run(self, output_emitter: tts.AudioEmitter):
        loop = asyncio.get_event_loop()

        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(
                    text=self._text,
                    voice=self._tts.voice,
                    rate=self._tts.rate,
                    volume=self._tts.volume,
                    connect_timeout=10,
                    receive_timeout=60,
                )

                # Collect all MP3 audio data
                mp3_buf = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        mp3_buf.write(chunk["data"])

                mp3_bytes = mp3_buf.getvalue()
                if not mp3_bytes:
                    return

                # Decode MP3 -> PCM16 in thread executor (non-blocking)
                def decode():
                    decoded = miniaudio.decode(
                        mp3_bytes,
                        nchannels=LIVEKIT_CHANNELS,
                        sample_rate=LIVEKIT_SAMPLE_RATE,
                        output_format=miniaudio.SampleFormat.SIGNED16,
                    )
                    return decoded.samples.tobytes()

                pcm_bytes = await loop.run_in_executor(None, decode)

                # Emit the full synthesized audio
                output_emitter.emit(
                    SynthesizedAudio(
                        request_id=utils.shortuuid(),
                        segment_id=utils.shortuuid(),
                        audio=self._tts.create_audio_frame(pcm_bytes),
                    )
                )
                return  # success

            except Exception as e:
                print(f"[EdgeTTS] Attempt {attempt + 1}/3 failed: {type(e).__name__}: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0)
                else:
                    print("[EdgeTTS] All retries exhausted. Skipping sentence.")
