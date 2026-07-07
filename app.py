"""
HUNTERS — LiveKit Agent Entrypoint

This is the main LiveKit Agent Worker for Hunter.
It connects to LiveKit Cloud and runs as a VoicePipelineAgent:

Pipeline:
  Mic (WebRTC) → Silero VAD → Whisper STT → Llama 3.1 LLM → Edge TTS → Speaker (WebRTC)

Run with:
  python app.py start    # Connect to LiveKit Cloud as a worker
  python app.py dev      # Hot-reload dev mode
  python app.py console  # Local terminal text mode (no LiveKit room needed)
"""

import os
import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import openai as lk_openai
from livekit.plugins import silero

from voice.livekit_plugins.whisper_stt import WhisperSTT
from voice.livekit_plugins.edge_tts_plugin import EdgeTTS
from prompts.hunter_prompts import HUNTER_SYSTEM_PROMPT, HUNTER_GREETING

load_dotenv()
logger = logging.getLogger("hunters")

# ─── LLM via HuggingFace (OpenAI-compatible, 100% free) ─────────────────────
def create_llm():
    """
    Uses livekit-plugins-openai pointed at HuggingFace's OpenAI-compatible API.
    This is completely free — it routes to HuggingFace, not OpenAI.
    """
    return lk_openai.LLM.with_base_url(
        base_url="https://api-inference.huggingface.co/v1",
        api_key=os.environ["HUGGING_FACE_API"],
        model="meta-llama/Llama-3.1-8B-Instruct",
        temperature=0.7,
    )


# ─── Agent Session Entrypoint ────────────────────────────────────────────────
async def entrypoint(ctx: JobContext):
    """Called when a new participant joins a LiveKit room."""
    await ctx.connect()
    logger.info("Hunter connected to room: %s", ctx.room.name)

    # Initial chat context (system prompt)
    initial_ctx = ChatContext().append(
        role="system",
        text=HUNTER_SYSTEM_PROMPT,
    )

    agent = Agent(instructions=HUNTER_SYSTEM_PROMPT)

    session = AgentSession(
        stt=WhisperSTT(),
        llm=create_llm(),
        tts=EdgeTTS(),
        vad=silero.VAD.load(),
        chat_ctx=initial_ctx,
    )

    # Print all transcript events to terminal
    @session.on("user_speech_committed")
    def on_user_speech(event):
        print(f"\n[You] {event.transcript}")

    @session.on("agent_speech_committed")
    def on_agent_speech(event):
        print(f"[Hunter] {event.transcript}\n")

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )

    # Greet the user on connection
    await session.say(HUNTER_GREETING, allow_interruptions=True)


# ─── Main: run the LiveKit Worker ────────────────────────────────────────────
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
