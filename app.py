import typer
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich import print as rprint
import time
import os

from voice.listener import Listener
from voice.whisper_engine import WhisperEngine
from voice.tts import TTSEngine
from agents.hunter import HunterAgent

app = typer.Typer()
console = Console()

@app.command()
def start():
    """Starts the Hunter Voice Assistant Loop."""
    console.clear()
    console.print(Panel.fit("[bold blue]Hunter System Initialization[/bold blue]", border_style="blue"))
    
    with console.status("[bold green]Loading components...[/bold green]"):
        tts = TTSEngine()
        listener = Listener()
        whisper = WhisperEngine()
        hunter = HunterAgent()
        
    console.clear()
    console.print(Panel("[bold green]System Ready. Press ENTER to speak, or type 'exit' to quit.[/bold green]"))
    
    tts.speak("Hunter is online and ready.")
    
    while True:
        try:
            user_input = console.input("\n[bold yellow]>[/bold yellow] ")
            if user_input.strip().lower() in ['exit', 'quit']:
                console.print("[bold red]Shutting down Hunter.[/bold red]")
                break
                
            # Listen
            console.print("[cyan]Listening...[/cyan]")
            audio_file = listener.listen_and_save()
            
            if not audio_file:
                continue
                
            # Transcribe
            console.print("[cyan]Transcribing...[/cyan]")
            user_text = whisper.transcribe(audio_file)
            
            if not user_text:
                console.print("[red]Could not understand audio.[/red]")
                continue
                
            console.print(Panel(user_text, title="You", border_style="green"))
            
            # Generate Response
            with console.status("[bold magenta]Hunter is thinking...[/bold magenta]"):
                hunter_response = hunter.respond(user_text)
                
            console.print(Panel(hunter_response, title="Hunter", border_style="blue"))
            
            # Speak Response
            tts.speak(hunter_response)
            
            # Cleanup temporary audio
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted by user. Exiting...[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")

if __name__ == "__main__":
    app()
