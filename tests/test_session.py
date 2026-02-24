import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from chatbot_tui.session import SessionManager, Session, Message


@pytest.fixture
def temp_dir():
    """Create a temporary directory for sessions."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def session_manager(temp_dir):
    """Create a SessionManager with a temporary directory."""
    return SessionManager(sessions_dir=temp_dir)


class TestMessage:
    """Test Message dataclass."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_message_to_dict(self):
        """Test converting message to dict."""
        msg = Message(role="user", content="Hello")
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Hello"
        assert "timestamp" in data

    def test_message_from_dict(self):
        """Test creating message from dict."""
        data = {
            "role": "user",
            "content": "Hello",
            "timestamp": "2025-02-24T12:00:00"
        }
        msg = Message.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestSession:
    """Test Session class."""

    def test_create_session(self):
        """Test creating a new session."""
        session = Session()
        assert session.id is not None
        assert session.messages == []
        assert session.created_at is not None
        assert session.system_prompt is None

    def test_create_session_with_system_prompt(self):
        """Test creating a session with a system prompt."""
        session = Session(system_prompt="You are helpful.")
        assert session.system_prompt == "You are helpful."

    def test_add_message(self):
        """Test adding a message to a session."""
        session = Session()
        msg = Message(role="user", content="Hello")
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0] == msg

    def test_session_to_dict(self):
        """Test converting session to dict."""
        session = Session()
        session.add_message(Message(role="user", content="Hello"))
        data = session.to_dict()
        assert "id" in data
        assert "messages" in data
        assert "created_at" in data
        assert len(data["messages"]) == 1

    def test_session_from_dict(self):
        """Test creating session from dict."""
        data = {
            "id": "test-id",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-02-24T12:00:00"}
            ],
            "created_at": "2025-02-24T12:00:00",
            "system_prompt": None
        }
        session = Session.from_dict(data)
        assert session.id == "test-id"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"

    def test_get_messages_for_api(self):
        """Test getting messages formatted for API."""
        session = Session(system_prompt="Be helpful")
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi there"))

        api_messages = session.get_messages_for_api()
        assert len(api_messages) == 3  # system + 2 messages
        assert api_messages[0] == {"role": "system", "content": "Be helpful"}
        assert api_messages[1] == {"role": "user", "content": "Hello"}
        assert api_messages[2] == {"role": "assistant", "content": "Hi there"}


class TestSessionManager:
    """Test SessionManager class."""

    def test_create_session(self, session_manager):
        """Test creating a new session."""
        session = session_manager.create_session()
        assert session.id is not None
        assert session in session_manager.list_sessions()

    def test_create_session_with_system_prompt(self, session_manager):
        """Test creating a session with system prompt."""
        session = session_manager.create_session(system_prompt="Be helpful")
        assert session.system_prompt == "Be helpful"

    def test_list_sessions_initial(self, session_manager):
        """Test listing sessions when initially created."""
        sessions = session_manager.list_sessions()
        # SessionManager creates an initial session
        assert len(sessions) == 1

    def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        initial_count = len(session_manager.list_sessions())
        s1 = session_manager.create_session()
        s2 = session_manager.create_session()
        sessions = session_manager.list_sessions()
        assert len(sessions) == initial_count + 2

    def test_get_session(self, session_manager):
        """Test getting a session by ID."""
        s1 = session_manager.create_session()
        retrieved = session_manager.get_session(s1.id)
        assert retrieved.id == s1.id

    def test_get_session_not_found(self, session_manager):
        """Test getting a non-existent session."""
        with pytest.raises(KeyError):
            session_manager.get_session("non-existent")

    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        s1 = session_manager.create_session()
        session_manager.delete_session(s1.id)
        assert s1 not in session_manager.list_sessions()

    def test_delete_current_session_promotes_new(self, session_manager):
        """Test deleting current session sets new current."""
        s1 = session_manager.create_session()
        s2 = session_manager.create_session()
        original_current = session_manager.current_session
        session_manager.current_session = s1
        session_manager.delete_session(s1.id)
        # Should promote to another session, not necessarily s2 since order matters
        assert session_manager.current_session is not None
        assert session_manager.current_session.id != s1.id

    def test_delete_current_session_when_only_one(self, session_manager):
        """Test deleting the only session creates a new one."""
        s1 = session_manager.create_session()
        session_manager.delete_session(s1.id)
        assert session_manager.current_session is not None
        assert session_manager.current_session.id != s1.id

    def test_switch_to_session(self, session_manager):
        """Test switching to a different session."""
        s1 = session_manager.create_session()
        s2 = session_manager.create_session()
        session_manager.switch_to_session(s2.id)
        assert session_manager.current_session == s2

    def test_switch_to_nonexistent_session(self, session_manager):
        """Test switching to a non-existent session raises error."""
        with pytest.raises(KeyError):
            session_manager.switch_to_session("non-existent")

    def test_save_session(self, session_manager, temp_dir):
        """Test saving a session to disk."""
        session = session_manager.create_session()
        session.add_message(Message(role="user", content="Hello"))
        session_manager.save_session(session)

        # Check file exists
        expected_path = temp_dir / f"{session.id}.json"
        assert expected_path.exists()

        # Check content
        data = json.loads(expected_path.read_text())
        assert data["id"] == session.id
        assert len(data["messages"]) == 1

    def test_load_session(self, session_manager, temp_dir):
        """Test loading a session from disk."""
        session = session_manager.create_session()
        session.add_message(Message(role="user", content="Hello"))
        session_manager.save_session(session)

        # Clear and reload
        session_manager._sessions.clear()
        loaded = session_manager.load_session(session.id)
        assert loaded.id == session.id
        assert len(loaded.messages) == 1

    def test_load_all_sessions(self, session_manager, temp_dir):
        """Test loading all sessions from directory."""
        s1 = session_manager.create_session()
        s1.add_message(Message(role="user", content="Hello"))
        session_manager.save_session(s1)

        s2 = session_manager.create_session()
        s2.add_message(Message(role="user", content="Hi"))
        session_manager.save_session(s2)

        # Clear and reload
        session_manager._sessions.clear()
        session_manager.load_all_sessions()
        sessions = session_manager.list_sessions()
        assert len(sessions) == 2
