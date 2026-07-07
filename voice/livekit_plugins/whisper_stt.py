"""
HUNTERS — LiveKit Custom STT Plugin (Whisper)

Wraps our existing WhisperEngine to implement livekit.agents.stt.STT interface.
LiveKit handles mic capture and VAD; this class just receives audio frames
and returns transcriptions.
"""

import asyncio
from dataclasses import dataclass
from typing import AsyncIterable

import numpy as np
from livekit import rtc
from livekit.agents import stt, utils
from livekit.agents.stt import SpeechEvent, SpeechEventType, SpeechData

from voice.whisper_engine import WhisperEngine


class WhisperSTT(stt.STT):
    """
    LiveKit STT plugin wrapping our local faster-whisper engine.
    Receives buffered audio from LiveKit's VAD and transcribes it.
    """

    def __init__(self):
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._whisper = WhisperEngine()

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: str | None = None,
        conn_options: stt.SpeechRecognitionOptions | None = None,
    ) -> SpeechEvent:
        # Convert LiveKit AudioBuffer to a flat float32 numpy array
        audio_data = np.frombuffer(
            bytes(buffer),
            dtype=np.int16,
        ).astype(np.float32) / 32768.0

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, self._whisper.transcribe_buffer, audio_data)

        return SpeechEvent(
            type=SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[SpeechData(text=text.strip(), language="en")],
        )

    def stream(self, *, language: str | None = None, conn_options=None):
        raise NotImplementedError("WhisperSTT does not support streaming mode. Use with VAD.")
