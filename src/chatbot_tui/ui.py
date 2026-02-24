"""UI module for the TUI chatbot using Rich."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from chatbot_tui.session import Session, Message


class ChatUI:
    """User interface for the TUI chatbot."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the ChatUI.

        Args:
            console: Optional Rich Console instance (created if not provided)
        """
        self.console = console or Console()
        self.streaming_content = ""

    def _format_user_message(self, message: Message) -> Text:
        """Format a user message for display.

        Args:
            message: The user message to format

        Returns:
            Formatted Text object
        """
        # Create styled text
        text = Text()
        text.append("You", style="bold cyan")
        text.append(f" ({self._format_time(message.timestamp)})", style="dim cyan")
        text.append(": ", style="cyan")
        text.append(message.content, style="cyan")

        return text

    def _format_assistant_message(self, message: Message) -> Panel:
        """Format an assistant message for display.

        Args:
            message: The assistant message to format

        Returns:
            Formatted Panel with Markdown content
        """
        # Render markdown content
        markdown = Markdown(message.content)
        return Panel(
            markdown,
            title=":robot: Assistant",
            title_align="left",
            border_style="green",
            padding=(0, 1),
        )

    def _format_time(self, timestamp: str) -> str:
        """Format a timestamp for display.

        Args:
            timestamp: ISO format timestamp

        Returns:
            Formatted time string (HH:MM)
        """
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except (ValueError, TypeError):
            return "??:??"

    def _render_conversation(self, session: Session, streaming: bool = False) -> Panel:
        """Render the conversation for display in Live view.

        Args:
            session: The session to render
            streaming: Whether to include streaming content

        Returns:
            Panel containing the rendered conversation
        """
        content = []

        for message in session.messages:
            if message.role == "user":
                content.append(self._format_user_message(message))
            elif message.role == "assistant":
                content.append(self._format_assistant_message(message))
            content.append("")  # Spacing

        # Add streaming content if present
        if streaming and self.streaming_content:
            streaming_panel = Panel(
                Markdown(self.streaming_content),
                title=":robot: Assistant",
                title_align="left",
                border_style="dim green",
                padding=(0, 1),
            )
            content.append(streaming_panel)

        # If no messages, show welcome
        if not session.messages and not streaming:
            content.append(
                Text(
                    "Start a conversation by typing a message below.",
                    style="dim italic",
                )
            )

        # Use Group to combine renderables instead of fit=False
        from rich.console import Group

        return Panel(
            Group(*content),
            title=":speech_balloon: Chat",
            title_align="left",
            border_style="blue",
            padding=(0, 1),
        )

    def add_streaming_content(self, chunk: str) -> None:
        """Add content to the streaming buffer.

        Args:
            chunk: Content chunk to add
        """
        self.streaming_content += chunk

    def clear_streaming_content(self) -> None:
        """Clear the streaming buffer."""
        self.streaming_content = ""

    def display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="bold")
        welcome_text.append("ChatBot TUI", style="bold blue")
        welcome_text.append("!\n\n", style="bold")
        welcome_text.append(
            "Commands: /new, /list, /switch <id>, /delete <id>, /exit\n",
            style="dim",
        )

        self.console.print(Panel(welcome_text, border_style="blue"))

    def display_error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: Error message to display
        """
        self.console.print(Panel(message, title=":warning: Error", border_style="red"))

    def display_info(self, message: str) -> None:
        """Display an info message.

        Args:
            message: Info message to display
        """
        self.console.print(
            Panel(message, title=":information_source:", border_style="yellow")
        )

    def get_user_input(self) -> str:
        """Get user input from stdin.

        Returns:
            The user's input string
        """
        return Prompt.ask(
            "\n[bold cyan]You[/bold cyan]",
            console=self.console,
            default="",
            show_default=False,
        )

    def display_session_info(self, session: Session) -> None:
        """Display information about the current session.

        Args:
            session: The session to display info for
        """
        info = Text()
        info.append("Session ID: ", style="dim")
        info.append(session.id[:8], style="bold")
        info.append(f"\nMessages: {len(session.messages)}", style="dim")
        info.append(f"\nCreated: {self._format_time(session.created_at)}", style="dim")

        self.console.print(
            Panel(info, title=":file_folder: Session", border_style="blue")
        )

    def display_sessions_list(self, sessions: list[Session], current_id: str) -> None:
        """Display a list of sessions.

        Args:
            sessions: List of sessions to display
            current_id: ID of the current session
        """
        from rich.console import Group

        content = []
        for i, session in enumerate(sessions):
            prefix = ":arrow_right: " if session.id == current_id else "  "
            text = Text()
            text.append(prefix, style="green" if session.id == current_id else "dim")
            text.append(f"{i + 1}. ", style="dim")
            text.append(session.id[:8], style="bold")
            text.append(f" ({len(session.messages)} messages)", style="dim")
            content.append(text)

        self.console.print(
            Panel(
                Group(*content),
                title=":file_folder: Sessions",
                border_style="blue",
            )
        )
