"""
HUNTERS — v3 Terminal Client

Client for Text Mode (Local) and Voice Mode (Client-Server WebSocket).
"""

import sys
import asyncio
import json
import io
import soundfile as sf

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

import websockets

from voice.vad_listener import VADListener
from voice.audio_stream import SpeakerStream
from voice.stream_tts import StreamingTTS, stream_llm_to_speech
from agents.hunter import HunterAgent
from cli.stream_display import StreamDisplay
from config.settings import WS_SERVER_URL, VAD_SAMPLE_RATE

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Force standard output to UTF-8 to prevent cp1252 crashes with block characters
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = typer.Typer()
console = Console(highlight=False)

# ═══════════════════════════════════════════════════════════════════
#  VOICE MODE (WEBSOCKET CLIENT)
# ═══════════════════════════════════════════════════════════════════

async def async_run_voice_mode():
    display = StreamDisplay()
    display.print_static("\n[bold #3b82f6]  H U N T E R S  [/bold #3b82f6]", style="bold #3b82f6")
    display.print_static("  Voice Mode (Sarvam STT → Groq LLM → Edge TTS, all local TTS)", style="dim")
    display.print_static("  Press Ctrl+C to quit.\n", style="dim")

    vad = VADListener()
    speaker = SpeakerStream()
    await speaker.start()
    tts = StreamingTTS(speaker=speaker)

    display.start_live()

    # ── STARTUP GREETING ───────────────────────────────────────────
    greeting = "Hello Sir, All Systems are online, how may I assist you today?"
    display.show_status("Speaking...")
    display.stream_token(greeting)
    play_task = asyncio.create_task(speaker.play_all())
    await tts.speak_sentence(greeting)
    await speaker.play(None)
    await play_task
    display.clear_response()
    # ───────────────────────────────────────────────────────────────

    try:
        async with websockets.connect(WS_SERVER_URL) as ws:
            display.show_status("Ready (Speak now)")
            is_processing = False

            while True:
                # ── 1. Listen (only when not processing) ───────────
                display.show_status("Listening...")
                audio_np = await vad.listen()

                if len(audio_np) == 0 or is_processing:
                    continue

                is_processing = True
                display.show_status("Processing...")

                # ── 2. Encode WAV and send to server ───────────────
                wav_io = io.BytesIO()
                sf.write(wav_io, audio_np, VAD_SAMPLE_RATE, format='WAV', subtype='PCM_16')
                wav_bytes = wav_io.getvalue()
                await ws.send(json.dumps({"type": "audio"}))
                await ws.send(wav_bytes)

                display.clear_response()

                # ── 3. Create async generator from WS token stream ─
                async def ws_token_generator():
                    """Yields LLM tokens from the server, handles status/stt side-effects."""
                    while True:
                        msg = await ws.recv()
                        if not isinstance(msg, str):
                            continue
                        data = json.loads(msg)
                        msg_type = data.get("type")

                        if msg_type == "llm_token":
                            yield data["text"]
                        elif msg_type == "llm_done":
                            return                          # stops the generator
                        elif msg_type == "status":
                            display.show_status(data["text"])
                        elif msg_type == "stt_result":
                            display.show_user(data["text"])
                        elif msg_type == "error":
                            display.stream_token(f" [Error: {data.get('text', '?')}]")
                            return

                # ── 4. Run TTS locally, streaming tokens as they arrive ─
                display.show_status("Thinking...")
                play_task = asyncio.create_task(speaker.play_all())

                await stream_llm_to_speech(
                    token_generator=ws_token_generator(),
                    tts=tts,
                    on_token=lambda t: (display.stream_token(t), display.show_status("Speaking..."))[0],
                )

                # Wait for all queued audio to finish playing
                await speaker.play(None)
                await play_task

                is_processing = False
                display.show_status("Ready (Speak now)")

    except websockets.exceptions.ConnectionClosedError:
        display.print_static("\n[bold red]Connection to Voice Server closed unexpectedly.[/bold red]")
    except ConnectionRefusedError:
        display.print_static("\n[bold red]Could not connect to Voice Server.[/bold red]")
        display.print_static("Ensure `python server/voice_server.py` is running.")
    except KeyboardInterrupt:
        pass
    finally:
        display.stop_live()
        vad.cleanup()
        speaker.cleanup()
        display.print_static("\n[bold red]Hunter offline.[/bold red]")

# ═══════════════════════════════════════════════════════════════════
#  TEXT MODE (LOCAL CLI)
# ═══════════════════════════════════════════════════════════════════

async def async_run_text_mode():
    display = StreamDisplay()
    display.print_static("\n[bold blue]  H U N T E R S  [/bold blue]", style="bold blue")
    display.print_static("  Text Mode (Groq LLM + Edge TTS Local)", style="dim")
    display.print_static("  Type your messages and press Enter. Type 'exit' to quit.\n", style="dim")
    
    hunter = HunterAgent()
    speaker = SpeakerStream()
    await speaker.start()
    tts = StreamingTTS(speaker=speaker)
    
    display.start_live()
    
    # ── STARTUP GREETING ──
    greeting = "Hello Sir, All Systems are online, how may I assist you today?"
    display.show_status("Speaking...")
    display.stream_token(greeting)
    
    await tts.speak_full(greeting)
    await speaker.drain()
    display.clear_response()
    # ──────────────────────
    
    display.show_status("Ready")

    try:
        while True:
            display.stop_live()
            user_input = Prompt.ask("\n[bold yellow]>[/bold yellow] ")
            if user_input.strip().lower() in ['exit', 'quit']:
                break
                
            display.start_live()
            display.clear_response()
            display.show_user(user_input)
            display.show_status("Thinking...")

            def on_token(t):
                display.stream_token(t)
                display.show_status("Speaking...")

            # Start audio consumer concurrently so TTS plays while LLM streams
            play_task = asyncio.create_task(speaker.play_all())

            await stream_llm_to_speech(
                token_generator=hunter.respond_stream(user_input),
                tts=tts,
                on_token=on_token
            )

            # Sentinel to stop the player, then wait for all audio to finish
            await speaker.play(None)
            await play_task
            display.show_status("Ready")

    except KeyboardInterrupt:
        pass
    finally:
        display.stop_live()
        speaker.cleanup()
        display.print_static("\n[bold red]Hunter offline.[/bold red]")

# ═══════════════════════════════════════════════════════════════════
#  CLI MENU
# ═══════════════════════════════════════════════════════════════════

@app.command()
def start(
    mode: str = typer.Option(None, "--mode", "-m", help="Input mode: 'voice' or 'text'"),
):
    """Start the Hunter Assistant."""
    console.clear()

    if mode not in ["voice", "text"]:
        # ── Welcome Panel ──────────────────────────────────────────
        welcome_panel = Panel.fit(
            " [bold #3b82f6]*[/bold #3b82f6] Welcome to [bold white]Hunters[/bold white] ",
            border_style="#3b82f6"
        )
        console.print(welcome_panel)
        
        # ── Custom Pixel Art 3D Logo (Gemini Style) ───────────────
        base_logo = [
            "██   ██  ██   ██  ███   ██  ████████  ███████   ██████    ███████ ",
            "██   ██  ██   ██  ████  ██     ██     ██        ██   ██   ██      ",
            "███████  ██   ██  ██ ██ ██     ██     █████     ██████    ███████ ",
            "██   ██  ██   ██  ██  ████     ██     ██        ██   ██        ██ ",
            "██   ██  ███████  ██   ███     ██     ███████   ██   ██   ███████ "
        ]
        
        from rich.text import Text
        logo_text = Text()
        w = len(base_logo[0])
        h = len(base_logo)
        
        for y in range(h + 1):
            for x in range(w + 1):
                is_main = y < h and x < w and base_logo[y][x] == '█'
                is_shadow = False
                if not is_main:
                    # Drop shadow offset by +1x, +1y
                    if y > 0 and x > 0 and y - 1 < h and x - 1 < w and base_logo[y-1][x-1] == '█':
                        is_shadow = True
                    elif y > 0 and y - 1 < h and x < w and base_logo[y-1][x] == '█':
                        is_shadow = True
                    elif x > 0 and y < h and x - 1 < w and base_logo[y][x-1] == '█':
                        is_shadow = True
                        
                if is_main:
                    logo_text.append("█", style="#3b82f6") # Vibrant blue main face
                elif is_shadow:
                    logo_text.append("█", style="#1e3a8a") # Dark blue drop shadow
                else:
                    logo_text.append(" ")
            logo_text.append("\n")
            
        console.print(logo_text)
        
        # ── Mode Selection ─────────────────────────────────────────
        console.print("  [bold #3b82f6]1.[/bold #3b82f6] Voice Mode (Microphone + Sarvam STT)")
        console.print("  [bold #3b82f6]2.[/bold #3b82f6] Text Mode  (Keyboard + Local TTS)")
        console.print()

        choice = Prompt.ask(
            "Press [bold white]Enter[/bold white] for Voice, [bold white]2[/bold white] for Text",
            choices=["1", "2", ""],
            default="1",
            show_choices=False,
            show_default=False
        )
        mode = "voice" if choice in ["1", ""] else "text"
        console.clear()

    if mode == "text":
        asyncio.run(async_run_text_mode())
    else:
        asyncio.run(async_run_voice_mode())

if __name__ == "__main__":
    app()
