"""
HUNTERS — Centralized configuration settings.
All tunable parameters for voice pipeline, LLM, and CLI.
"""

# ─── Voice Pipeline Mode ──────────────────────────────────────────
VOICE_MODE = "streaming"  # "streaming" (new) or "legacy" (old pyttsx3 pipeline)

# ─── VAD (Voice Activity Detection) ───────────────────────────────
VAD_SAMPLE_RATE = 16000       # 16kHz — required by Silero VAD + Whisper
VAD_CHUNK_MS = 32             # 32ms chunks for VAD processing
VAD_CHUNK_SIZE = 512          # 16000 * 0.032 = 512 samples per chunk
VAD_SILENCE_MS = 800          # How long to wait after speech stops (ms)
VAD_THRESHOLD = 0.5           # Speech probability threshold (0.0 - 1.0)
VAD_MIN_SPEECH_MS = 250       # Minimum speech duration to avoid false triggers

# ─── Whisper STT ──────────────────────────────────────────────────
WHISPER_MODEL = "small.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ─── LLM (HuggingFace) ───────────────────────────────────────────
LLM_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.7

# ─── Edge TTS ─────────────────────────────────────────────────────
EDGE_TTS_VOICE = "en-GB-RyanNeural"   # British male — J.A.R.V.I.S. style
EDGE_TTS_RATE = "+0%"                 # Speech rate adjustment
EDGE_TTS_VOLUME = "+0%"               # Volume adjustment

# ─── Audio Output ─────────────────────────────────────────────────
SPEAKER_SAMPLE_RATE = 24000   # Edge TTS output rate
SPEAKER_CHANNELS = 1
SPEAKER_SAMPLE_WIDTH = 2      # 16-bit (paInt16)

# ─── Sentence Chunker ────────────────────────────────────────────
SENTENCE_DELIMITERS = {'.', '!', '?'}
MIN_SENTENCE_LENGTH = 10      # Don't send tiny fragments to TTS
MAX_BUFFER_WORDS = 20         # Force flush after N words even without punctuation
