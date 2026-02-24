"""Main entry point for the TUI ChatBot."""

import asyncio
import os
import sys

from dotenv import load_dotenv

from chatbot_tui.llm import LLMClient, LLMError
from chatbot_tui.session import SessionManager, Message
from chatbot_tui.ui import ChatUI
from rich.console import Console
from rich.live import Live


def load_env_vars() -> tuple[str, str]:
    """Load environment variables.

    Returns:
        Tuple of (base_url, api_key)

    Raises:
        ValueError: If required environment variables are not set
    """
    load_dotenv()

    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    if not base_url:
        raise ValueError(
            "OPENAI_BASE_URL environment variable is not set. "
            "Create a .env file with OPENAI_BASE_URL and OPENAI_API_KEY."
        )

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Create a .env file with OPENAI_BASE_URL and OPENAI_API_KEY."
        )

    return base_url, api_key


def handle_command(
    command: str,
    args: str,
    session_manager: SessionManager,
    ui: ChatUI,
) -> bool:
    """Handle a slash command.

    Args:
        command: The command (without the slash)
        args: Arguments to the command
        session_manager: The session manager
        ui: The UI instance

    Returns:
        True if the program should exit, False otherwise
    """
    if command == "exit" or command == "quit":
        return True

    elif command == "new":
        session = session_manager.create_session()
        ui.display_info(f"Created new session: {session.id[:8]}")
        return False

    elif command == "list":
        sessions = session_manager.list_sessions()
        ui.display_sessions_list(sessions, session_manager.current_session.id)
        return False

    elif command == "switch":
        if not args:
            ui.display_error("Usage: /switch <session_id>")
            return False
        try:
            session_manager.switch_to_session(args)
            ui.display_info(f"Switched to session: {args[:8]}")
        except KeyError:
            ui.display_error(f"Session not found: {args}")
        return False

    elif command == "delete":
        if not args:
            ui.display_error("Usage: /delete <session_id>")
            return False
        try:
            session_manager.delete_session(args)
            ui.display_info(f"Deleted session: {args[:8]}")
        except KeyError:
            ui.display_error(f"Session not found: {args}")
        return False

    else:
        ui.display_error(f"Unknown command: /{command}")
        return False


async def run_chat_loop(
    llm_client: LLMClient,
    session_manager: SessionManager,
    ui: ChatUI,
) -> None:
    """Run the main chat loop.

    Args:
        llm_client: The LLM client
        session_manager: The session manager
        ui: The UI instance
    """
    ui.display_welcome()

    with Live(console=ui.console, refresh_per_second=4) as live:
        while True:
            # Update display
            live.update(ui._render_conversation(session_manager.current_session))

            # Get user input
            try:
                user_input = ui.get_user_input()
            except (EOFError, KeyboardInterrupt):
                break

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split(maxsplit=1)
                command = parts[0]
                args = parts[1] if len(parts) > 1 else ""

                should_exit = handle_command(command, args, session_manager, ui)
                if should_exit:
                    break
                continue

            # Add user message to session
            user_message = Message(role="user", content=user_input)
            session_manager.current_session.add_message(user_message)
            session_manager.save_session(session_manager.current_session)

            # Stream assistant response
            try:
                ui.clear_streaming_content()
                live.update(
                    ui._render_conversation(
                        session_manager.current_session, streaming=True
                    )
                )

                assistant_content = ""
                messages = session_manager.current_session.get_messages_for_api()

                async for chunk in llm_client.chat_stream(messages):
                    assistant_content += chunk
                    ui.add_streaming_content(chunk)
                    live.update(
                        ui._render_conversation(
                            session_manager.current_session, streaming=True
                        )
                    )

                # Add assistant message to session
                if assistant_content:
                    assistant_message = Message(
                        role="assistant", content=assistant_content
                    )
                    session_manager.current_session.add_message(assistant_message)
                    session_manager.save_session(session_manager.current_session)

                ui.clear_streaming_content()
                live.update(ui._render_conversation(session_manager.current_session))

            except LLMError as e:
                ui.display_error(f"LLM error: {e}")
                ui.clear_streaming_content()
                live.update(ui._render_conversation(session_manager.current_session))


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load environment variables
        base_url, api_key = load_env_vars()

        # Initialize components
        console = Console()
        ui = ChatUI(console=console)
        session_manager = SessionManager()
        llm_client = LLMClient(base_url=base_url, api_key=api_key)

        # Run the chat loop
        asyncio.run(run_chat_loop(llm_client, session_manager, ui))

        return 0

    except ValueError as e:
        console = Console()
        ui = ChatUI(console=console)
        ui.display_error(str(e))
        return 1

    except KeyboardInterrupt:
        # Silently exit on Ctrl+C
        return 0

    except Exception as e:
        console = Console()
        ui = ChatUI(console=console)
        ui.display_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
