"""
HUNTERS — Streaming CLI Display

Rich-based real-time terminal display.
Streams LLM output token-by-token and shows status indicators
for Listening, Thinking, and Speaking states.
"""

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.table import Table


class StreamDisplay:
    """
    Real-time CLI display using Rich Live.
    Updates the terminal flicker-free as tokens arrive.
    
    Layout:
    ┌──────────── HUNTERS ────────────┐
    │ 🟢 Status: Listening...         │
    ├─────────────────────────────────┤
    │ You: "user transcript"          │
    ├─────────────────────────────────┤
    │ Hunter: "streaming response..." │
    └─────────────────────────────────┘
    """

    def __init__(self):
        self.console = Console()
        self._status = "Initializing..."
        self._user_text = ""
        self._hunter_text = ""
        self._live = None

    def _build_display(self) -> Panel:
        """Build the Rich panel for the current state."""
        table = Table.grid(padding=(0, 1))
        table.add_column(ratio=1)

        # Status line
        status_color = {
            "Listening...": "green",
            "Processing...": "yellow",
            "Thinking...": "magenta",
            "Speaking...": "cyan",
            "Ready": "green",
        }.get(self._status, "white")
        
        status_icon = {
            "Listening...": "🎙",
            "Processing...": "⚙",
            "Thinking...": "🧠",
            "Speaking...": "🗣",
            "Ready": "🟢",
        }.get(self._status, "⚪")

        table.add_row(
            Text(f" {status_icon}  {self._status}", style=f"bold {status_color}")
        )
        table.add_row(Text("─" * 50, style="dim"))

        # User transcript
        if self._user_text:
            table.add_row(
                Text(f" You:  {self._user_text}", style="green")
            )
            table.add_row(Text("─" * 50, style="dim"))

        # Hunter response (streaming)
        if self._hunter_text:
            # Show cursor if still streaming
            display_text = self._hunter_text
            if self._status in ("Thinking...", "Speaking..."):
                display_text += " ▊"
            table.add_row(
                Text(f" Hunter:  {display_text}", style="bold blue")
            )

        return Panel(
            table,
            title="[bold blue]H U N T E R S[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

    def start_live(self):
        """Start the Rich Live display."""
        self._live = Live(
            self._build_display(),
            console=self.console,
            refresh_per_second=15,
            transient=False,
        )
        self._live.start()

    def stop_live(self):
        """Stop the Rich Live display."""
        if self._live:
            self._live.stop()
            self._live = None

    def _refresh(self):
        """Refresh the live display."""
        if self._live:
            self._live.update(self._build_display())

    def show_status(self, status: str):
        """Update the status indicator."""
        self._status = status
        self._refresh()

    def show_user(self, text: str):
        """Display the user's transcribed speech."""
        self._user_text = text
        self._refresh()

    def stream_token(self, token: str):
        """Append a single token to Hunter's response (called per SSE token)."""
        self._hunter_text += token
        self._refresh()

    def clear_response(self):
        """Clear Hunter's response for the next turn."""
        self._hunter_text = ""
        self._user_text = ""
        self._refresh()

    def print_static(self, text: str, style: str = "white"):
        """Print a static line outside the live display."""
        self.console.print(text, style=style)


# ─── Standalone display (no live, for legacy mode) ────────────────

class LegacyDisplay:
    """Simple non-live display for the legacy pipeline."""

    def __init__(self):
        self.console = Console()

    def show_status(self, status: str):
        self.console.print(f"[cyan]{status}[/cyan]")

    def show_user(self, text: str):
        self.console.print(Panel(text, title="You", border_style="green"))

    def show_hunter(self, text: str):
        self.console.print(Panel(text, title="Hunter", border_style="blue"))

    def print_static(self, text: str, style: str = "white"):
        self.console.print(text, style=style)
