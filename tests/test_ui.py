import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from chatbot_tui.ui import ChatUI
from chatbot_tui.session import Message, Session


@pytest.fixture
def chat_ui():
    """Create a ChatUI with a real console (for renderable objects)."""
    from rich.console import Console
    # Use a file console to avoid terminal issues in tests
    import io
    console = Console(file=io.StringIO(), width=100, force_terminal=True)
    return ChatUI(console=console)


class TestChatUI:
    """Test ChatUI class."""

    def test_init(self, chat_ui):
        """Test UI initialization."""
        assert chat_ui.console is not None
        assert chat_ui.streaming_content == ""

    def test_format_user_message(self, chat_ui):
        """Test formatting a user message."""
        msg = Message(role="user", content="Hello")
        formatted = chat_ui._format_user_message(msg)
        # Check that it returns a Text object with the content
        assert "Hello" in formatted.plain
        assert "You" in formatted.plain

    def test_format_assistant_message(self, chat_ui):
        """Test formatting an assistant message."""
        msg = Message(role="assistant", content="Hi there!")
        formatted = chat_ui._format_assistant_message(msg)
        # Should return a Panel
        assert formatted is not None
        assert formatted.title == ":robot: Assistant"

    def test_format_assistant_message_with_markdown(self, chat_ui):
        """Test formatting assistant message with Markdown."""
        msg = Message(role="assistant", content="Hello **world**!")
        formatted = chat_ui._format_assistant_message(msg)
        # Should handle markdown
        assert formatted is not None

    def test_format_assistant_message_with_code(self, chat_ui):
        """Test formatting assistant message with code block."""
        msg = Message(role="assistant", content="Here's code:\n```python\nprint('hello')\n```")
        formatted = chat_ui._format_assistant_message(msg)
        # Should handle code blocks
        assert formatted is not None

    def test_render_conversation_empty(self, chat_ui):
        """Test rendering empty conversation."""
        session = Session()
        rendered = chat_ui._render_conversation(session)
        # Empty conversation should render a Panel
        assert rendered is not None
        assert rendered.title == ":speech_balloon: Chat"

    def test_render_conversation_with_messages(self, chat_ui):
        """Test rendering conversation with messages."""
        session = Session()
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi there!"))
        rendered = chat_ui._render_conversation(session)
        assert rendered is not None

    def test_add_streaming_content(self, chat_ui):
        """Test adding streaming content."""
        chat_ui.add_streaming_content("Hello")
        assert chat_ui.streaming_content == "Hello"
        chat_ui.add_streaming_content(" world")
        assert chat_ui.streaming_content == "Hello world"

    def test_clear_streaming_content(self, chat_ui):
        """Test clearing streaming content."""
        chat_ui.add_streaming_content("Hello")
        chat_ui.clear_streaming_content()
        assert chat_ui.streaming_content == ""

    def test_render_with_streaming(self, chat_ui):
        """Test rendering with streaming content."""
        session = Session()
        session.add_message(Message(role="user", content="Hello"))
        chat_ui.add_streaming_content("Hi...")
        rendered = chat_ui._render_conversation(session, streaming=True)
        assert rendered is not None

    def test_display_welcome(self, chat_ui):
        """Test displaying welcome message."""
        # Just check it doesn't crash
        chat_ui.display_welcome()

    def test_display_error(self, chat_ui):
        """Test displaying error message."""
        chat_ui.display_error("Something went wrong")

    def test_get_user_input_with_mock(self, chat_ui):
        """Test getting user input with mocked Prompt."""
        with patch('chatbot_tui.ui.Prompt.ask', return_value="Hello"):
            result = chat_ui.get_user_input()
            assert result == "Hello"

    def test_get_user_input_empty_with_mock(self, chat_ui):
        """Test getting empty user input with mocked Prompt."""
        with patch('chatbot_tui.ui.Prompt.ask', return_value=""):
            result = chat_ui.get_user_input()
            assert result == ""

    def test_display_session_info(self, chat_ui):
        """Test displaying session information."""
        session = Session()
        chat_ui.display_session_info(session)

    def test_display_sessions_list(self, chat_ui):
        """Test displaying list of sessions."""
        sessions = [Session(), Session()]
        chat_ui.display_sessions_list(sessions, current_id=sessions[0].id)

    def test_format_time_valid(self, chat_ui):
        """Test formatting a valid timestamp."""
        result = chat_ui._format_time("2025-02-24T12:30:45")
        assert result == "12:30"

    def test_format_time_invalid(self, chat_ui):
        """Test formatting an invalid timestamp."""
        result = chat_ui._format_time("invalid")
        assert result == "??:??"

    def test_format_time_none(self, chat_ui):
        """Test formatting a None timestamp."""
        result = chat_ui._format_time(None)
        assert result == "??:??"
