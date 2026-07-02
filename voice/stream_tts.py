"""
HUNTERS — Streaming TTS Pipeline

Streaming text-to-speech using Edge TTS (free, neural voices).
Includes a sentence chunker that accumulates LLM tokens into sentences
and fires TTS for each sentence immediately — audio starts playing
while the LLM is still generating.

Flow:
  LLM token stream → SentenceChunker → Edge TTS (per sentence) → SpeakerStream
"""

import asyncio
import edge_tts
import miniaudio
from io import BytesIO

from voice.audio_stream import SpeakerStream
from config.settings import (
    EDGE_TTS_VOICE,
    EDGE_TTS_RATE,
    EDGE_TTS_VOLUME,
    SPEAKER_SAMPLE_RATE,
    SENTENCE_DELIMITERS,
    MIN_SENTENCE_LENGTH,
    MAX_BUFFER_WORDS,
)


class SentenceChunker:
    """
    Accumulates streaming tokens into complete sentences.
    Yields a sentence string each time a sentence boundary is detected.
    """

    def __init__(self):
        self._buffer = ""
        self._word_count = 0

    def feed(self, token: str):
        """Feed a token into the chunker."""
        self._buffer += token
        self._word_count += token.count(' ')

        # Check for sentence-ending punctuation
        for delimiter in SENTENCE_DELIMITERS:
            if delimiter in token:
                # Split precisely at the first delimiter found in the buffer
                parts = self._buffer.split(delimiter, 1)
                sentence = (parts[0] + delimiter).strip()
                remainder = parts[1] if len(parts) > 1 else ""

                if len(sentence) >= MIN_SENTENCE_LENGTH:
                    self._buffer = remainder
                    self._word_count = remainder.count(' ')
                    return sentence
        
        # Force flush if buffer is getting long without punctuation
        if self._word_count >= MAX_BUFFER_WORDS:
            sentence = self._buffer.strip()
            if sentence:
                self._buffer = ""
                self._word_count = 0
                return sentence

        return None

    def flush(self) -> str:
        """Flush any remaining text in the buffer."""
        sentence = self._buffer.strip()
        self._buffer = ""
        self._word_count = 0
        return sentence if sentence else None


class StreamingTTS:
    """
    Streaming text-to-speech using Microsoft Edge TTS.
    """

    def __init__(self, speaker: SpeakerStream = None):
        self.voice = EDGE_TTS_VOICE
        self.rate = EDGE_TTS_RATE
        self.volume = EDGE_TTS_VOLUME
        self.speaker = speaker
        self._is_speaking = False

    async def speak_sentence(self, text: str):
        """
        Synthesize a single sentence and stream audio to the speaker.
        Audio starts playing as soon as the first chunk arrives from Edge TTS.
        """
        if not text or not text.strip():
            return

        self._is_speaking = True
        loop = asyncio.get_event_loop()

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
            )

            # Collect audio chunks from Edge TTS (mp3 format)
            audio_data = BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])

            # Decode MP3 to PCM16 in an executor so it NEVER blocks the async event loop
            mp3_bytes = audio_data.getvalue()
            if len(mp3_bytes) > 0:
                def decode_audio():
                    # miniaudio is incredibly fast and resamples on-the-fly
                    decoded = miniaudio.decode(
                        mp3_bytes, 
                        nchannels=1, 
                        sample_rate=SPEAKER_SAMPLE_RATE,
                        output_format=miniaudio.SampleFormat.SIGNED16
                    )
                    return decoded.samples.tobytes()

                pcm_data = await loop.run_in_executor(None, decode_audio)

                if self.speaker:
                    await self.speaker.play(pcm_data)

        except Exception as e:
            print(f"Edge TTS error: {e}")
        finally:
            self._is_speaking = False

    async def speak_full(self, text: str):
        """
        Convenience method: speak an entire text block.
        Useful for greetings or short fixed responses.
        """
        await self.speak_sentence(text)
        if self.speaker:
            await self.speaker.play(None)  # Sentinel to signal end

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking


async def stream_llm_to_speech(
    token_generator,
    tts: StreamingTTS,
    on_token=None,
    on_sentence=None,
):
    """
    Core streaming pipeline: consumes LLM token generator,
    chunks into sentences, and fires TTS for each.
    
    Args:
        token_generator: Async generator yielding string tokens from the LLM.
        tts: StreamingTTS instance connected to a SpeakerStream.
        on_token: Optional callback(token: str) for CLI display updates.
        on_sentence: Optional callback(sentence: str) when a sentence completes.
    
    Returns:
        str: The full accumulated response text.
    """
    chunker = SentenceChunker()
    full_response = ""
    
    loop = asyncio.get_event_loop()
    
    async for token in token_generator:
        full_response += token

        # Notify CLI display
        if on_token:
            on_token(token)

        # Check if we have a complete sentence
        sentence = chunker.feed(token)
        if sentence:
            if on_sentence:
                on_sentence(sentence)
            # Fire TTS for this sentence (runs in background)
            await tts.speak_sentence(sentence)

    # Flush remaining text
    remaining = chunker.flush()
    if remaining:
        if on_sentence:
            on_sentence(remaining)
        await tts.speak_sentence(remaining)

    # Signal end of playback
    if tts.speaker:
        await tts.speaker.play(None)

    return full_response


# ─── Test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        speaker = SpeakerStream()
        await speaker.start()
        tts = StreamingTTS(speaker=speaker)

        # Simulate streaming tokens
        tokens = [
            "Right ", "then, ", "sir. ", "I'll ", "begin ", "the ", "hunt ", 
            "for ", "AI ", "internships ", "in ", "Bangalore. ",
            "This ", "should ", "be ", "quite ", "interesting!"
        ]

        def fake_token_gen():
            for t in tokens:
                yield t

        # Start playback consumer in background
        play_task = asyncio.create_task(speaker.play_all())

        full = await stream_llm_to_speech(
            fake_token_gen(),
            tts,
            on_token=lambda t: print(t, end="", flush=True),
        )

        await play_task
        print(f"\n\nFull response: {full}")
        speaker.cleanup()

    asyncio.run(test())
