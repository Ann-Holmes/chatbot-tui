"""Session management for multi-session chat history."""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class Message:
    """A chat message."""

    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=data["role"], content=data["content"], timestamp=data["timestamp"]
        )


@dataclass
class Session:
    """A chat session with message history."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    system_prompt: Optional[str] = None

    def add_message(self, message: Message) -> None:
        """Add a message to this session."""
        self.messages.append(message)

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "system_prompt": self.system_prompt,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """Create session from dictionary."""
        return cls(
            id=data["id"],
            messages=[Message.from_dict(m) for m in data["messages"]],
            created_at=data["created_at"],
            system_prompt=data.get("system_prompt"),
        )

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API call."""
        messages = [{"role": m.role, "content": m.content} for m in self.messages]
        if self.system_prompt:
            messages = [{"role": "system", "content": self.system_prompt}, *messages]
        return messages


class SessionManager:
    """Manager for multiple chat sessions with persistence."""

    def __init__(self, sessions_dir: Path = Path(".sessions")):
        """Initialize the session manager.

        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}
        self.current_session: Optional[Session] = None
        self.load_all_sessions()

        # Create initial session if none exist
        if not self._sessions:
            self.create_session()

    def create_session(self, system_prompt: Optional[str] = None) -> Session:
        """Create a new session.

        Args:
            system_prompt: Optional system prompt for the session

        Returns:
            The newly created session
        """
        session = Session(system_prompt=system_prompt)
        self._sessions[session.id] = session
        self.current_session = session
        return session

    def list_sessions(self) -> List[Session]:
        """List all sessions, sorted by creation time (newest first)."""
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def get_session(self, session_id: str) -> Session:
        """Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session

        Raises:
            KeyError: If session not found
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def switch_to_session(self, session_id: str) -> None:
        """Switch to a different session.

        Args:
            session_id: The session ID to switch to

        Raises:
            KeyError: If session not found
        """
        self.current_session = self.get_session(session_id)

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: The session ID to delete
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")

        # Delete from disk
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

        # Remove from memory
        del self._sessions[session_id]

        # If we deleted the current session, switch to another
        if self.current_session and self.current_session.id == session_id:
            if self._sessions:
                self.current_session = list(self._sessions.values())[0]
            else:
                self.current_session = self.create_session()

    def save_session(self, session: Session) -> None:
        """Save a session to disk.

        Args:
            session: The session to save
        """
        session_file = self.sessions_dir / f"{session.id}.json"
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def load_session(self, session_id: str) -> Session:
        """Load a session from disk.

        Args:
            session_id: The session ID to load

        Returns:
            The loaded session

        Raises:
            KeyError: If session file not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise KeyError(f"Session file for {session_id} not found")

        with open(session_file) as f:
            data = json.load(f)

        session = Session.from_dict(data)
        self._sessions[session_id] = session
        return session

    def load_all_sessions(self) -> None:
        """Load all sessions from the sessions directory."""
        if not self.sessions_dir.exists():
            return

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                self._sessions[session.id] = session
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted files
                continue

        # Set current session to most recent
        sessions = self.list_sessions()
        if sessions:
            self.current_session = sessions[0]
