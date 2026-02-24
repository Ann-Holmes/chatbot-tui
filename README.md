# ChatBot TUI

A terminal-based chatbot interface built with [Rich](https://rich.readthedocs.io/) and the OpenAI SDK.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 🎨 Beautiful TUI interface with Rich library
- 💬 Multi-session management with persistent history
- 📝 Markdown rendering with syntax highlighting
- ⚡ Real-time streaming responses (typewriter effect)
- 🔄 OpenAI-compatible API support
- 📁 Session persistence in JSON format
- 🎯 Slash commands for session management

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/Ann-Holmes/chatbot-tui.git
cd chatbot-tui

# Install dependencies
uv sync
```

## Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_BASE_URL` | Yes | Base URL for OpenAI-compatible API | - |
| `OPENAI_API_KEY` | Yes | API key for authentication | - |
| `OPENAI_MODEL` | No | Model name to use | `gpt-4o-mini` |

## Usage

### Starting the Chatbot

```bash
uv run python -m chatbot_tui.main
```

Or use the installed script:

```bash
uv run chatbot
```

### Slash Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/new` | Create a new session | `/new` |
| `/list` | List all sessions | `/list` |
| `/switch <id>` | Switch to a session | `/switch abc12345` |
| `/delete <id>` | Delete a session | `/delete abc12345` |
| `/exit` | Exit the application | `/exit` |

## Session Management

Sessions are automatically saved to the `.sessions/` directory in JSON format. Each session contains:

- Session ID (UUID)
- Message history
- Creation timestamp
- System prompt (optional)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_llm.py -v

# Run with coverage
uv run pytest --cov=chatbot_tui tests/
```

### Code Quality

```bash
# Format code
uv run ruff format src/ tests/

# Check and fix linting issues
uv run ruff check --fix src/ tests/
```

## Project Structure

```
chatbot-tui/
├── src/chatbot_tui/
│   ├── __init__.py
│   ├── main.py       # Entry point and main loop
│   ├── llm.py        # OpenAI SDK integration
│   ├── session.py    # Session management
│   └── ui.py         # Rich TUI interface
├── tests/
│   ├── test_llm.py
│   ├── test_session.py
│   └── test_ui.py
├── .sessions/        # Session storage (auto-created)
├── pyproject.toml
└── README.md
```

## Architecture

- **LLM Module** (`llm.py`): Handles OpenAI SDK integration with async streaming
- **Session Module** (`session.py`): Manages chat sessions and persistence
- **UI Module** (`ui.py`): Rich-based terminal interface with Live updates
- **Main Loop** (`main.py`): Coordinates components and handles user input

## License

MIT License

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass (`uv run pytest`)
2. Code is formatted (`uv run ruff format`)
3. No linting errors (`uv run ruff check`)
