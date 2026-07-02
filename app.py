"""
HUNTERS — Main Application Entry Point

Supports two modes (both use the streaming LLM + TTS pipeline):
  1. Voice Mode: VAD → Whisper buffer → LLM SSE → Edge TTS → Speaker
  2. Text Mode:  Keyboard Input → LLM SSE → Edge TTS → Speaker
"""

import typer
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

app = typer.Typer()
console = Console()


# ═══════════════════════════════════════════════════════════════════
#  TEXT MODE PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def run_text_mode():
    """
    Text input loop.
    Uses plain stdin — NO Rich Live display — to avoid stdin corruption.
    """
    from voice.audio_stream import SpeakerStream
    from voice.stream_tts import StreamingTTS, stream_llm_to_speech
    from agents.hunter import HunterAgent
    from prompts.hunter_prompts import HUNTER_GREETING

    console.print(Panel.fit("[bold blue]  H U N T E R S  [/bold blue]\n[dim]Text Mode — type your query, type [bold]exit[/bold] to quit[/dim]", border_style="blue"))
    console.print("[dim]Loading components...[/dim]")

    hunter = HunterAgent()
    speaker = SpeakerStream()
    await speaker.start()
    tts = StreamingTTS(speaker=speaker)

    console.print("[bold green]All systems online.[/bold green]\n")

    # ── Greeting ──
    console.print(f"[bold blue]Hunter:[/bold blue] {HUNTER_GREETING}")
    play_task = asyncio.create_task(speaker.play_all())
    await tts.speak_full(HUNTER_GREETING)
    await play_task

    loop = asyncio.get_event_loop()

    try:
        while True:
            # Plain input — no Rich Live, no executor tricks
            console.print("")
            try:
                user_text = await loop.run_in_executor(
                    None, lambda: input("You: ")
                )
            except (EOFError, KeyboardInterrupt):
                break

            user_text = user_text.strip()
            if not user_text:
                continue
            if user_text.lower() in ["exit", "quit"]:
                break

            console.print("")
            console.print("[bold blue]Hunter:[/bold blue] ", end="")

            # Start speaker playback consumer
            play_task = asyncio.create_task(speaker.play_all())

            # Stream tokens → TTS → speaker, print tokens inline
            full_response = await stream_llm_to_speech(
                token_generator=hunter.respond_stream(user_text),
                tts=tts,
                on_token=lambda token: print(token, end="", flush=True),
            )

            # Wait for audio to finish
            await play_task
            print()  # newline after streamed response

    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[bold red]Hunter offline.[/bold red]")
        speaker.cleanup()


# ═══════════════════════════════════════════════════════════════════
#  VOICE MODE PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def run_voice_mode():
    """
    Hands-free voice loop using VAD + Whisper + streaming LLM + Edge TTS.
    Uses Rich Live display for animated status updates.
    """
    from cli.stream_display import StreamDisplay
    from voice.audio_stream import SpeakerStream
    from voice.stream_tts import StreamingTTS, stream_llm_to_speech
    from voice.vad_listener import VADListener
    from voice.whisper_engine import WhisperEngine
    from agents.hunter import HunterAgent
    from prompts.hunter_prompts import HUNTER_GREETING
    from config.settings import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE

    display = StreamDisplay()
    display.print_static("\n[bold blue]  H U N T E R S  [/bold blue]", style="bold blue")
    display.print_static("  Voice Mode (Hands-free streaming)", style="dim")
    display.print_static("  Speak naturally — Hunter will listen automatically.\n", style="dim")
    display.print_static("[dim]Loading components...[/dim]")

    whisper = WhisperEngine(
        model_size=WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )
    hunter = HunterAgent()
    speaker = SpeakerStream()
    await speaker.start()
    tts = StreamingTTS(speaker=speaker)
    vad = VADListener()

    display.print_static("[bold green]All systems online.[/bold green]\n")

    # ── Greeting ──
    display.start_live()
    display.show_status("Speaking...")

    play_task = asyncio.create_task(speaker.play_all())
    await tts.speak_full(HUNTER_GREETING)
    await play_task

    loop = asyncio.get_event_loop()

    try:
        while True:
            display.clear_response()
            display.show_status("Listening...")

            audio_buffer = await vad.listen()
            if len(audio_buffer) == 0:
                continue

            display.show_status("Processing...")
            user_text = await loop.run_in_executor(
                None, whisper.transcribe_buffer, audio_buffer
            )

            if not user_text or not user_text.strip():
                continue

            display.show_user(user_text)
            display.show_status("Thinking...")

            play_task = asyncio.create_task(speaker.play_all())

            full_response = await stream_llm_to_speech(
                token_generator=hunter.respond_stream(user_text),
                tts=tts,
                on_token=lambda token: (
                    display.stream_token(token),
                    display.show_status("Speaking..."),
                ),
            )

            await play_task
            display.show_status("Ready")

    except KeyboardInterrupt:
        display.show_status("Shutting down...")
    finally:
        display.stop_live()
        display.print_static("\n[bold red]Hunter offline.[/bold red]")
        vad.cleanup()
        speaker.cleanup()


# ═══════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

@app.command()
def start(
    mode: str = typer.Option(None, "--mode", "-m", help="Input mode: 'voice' or 'text'"),
):
    """Start the Hunter Voice Assistant."""
    console.clear()

    if mode not in ["voice", "text"]:
        console.print(Panel.fit("[bold blue]HUNTERS[/bold blue]", border_style="blue"))
        console.print("Please select an input mode:")
        console.print("  [bold cyan]1.[/bold cyan] Voice Mode (Hands-free, uses microphone)")
        console.print("  [bold cyan]2.[/bold cyan] Text Mode (Type your queries)")

        choice = Prompt.ask("\nEnter your choice", choices=["1", "2"], default="1")
        mode = "voice" if choice == "1" else "text"
        console.clear()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if mode == "text":
        asyncio.run(run_text_mode())
    else:
        asyncio.run(run_voice_mode())


if __name__ == "__main__":
    app()
