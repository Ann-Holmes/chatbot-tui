# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python TUI ChatBot application built with [Rich](https://rich.readthedocs.io/) for terminal UI. The project uses `uv` for package management and environment handling.

## Development Commands

### Environment Setup
```bash
# Initialize project with uv (if not already done)
uv init

# Install dependencies
uv sync

# Run the application
uv run python main.py
```

### Environment Variables
The application requires these environment variables for LLM integration:
- `OPENAI_BASE_URL` - Base URL for the OpenAI-compatible API
- `OPENAI_API_KEY` - API key for authentication
- `OPENAI_MODEL` - Model name to use (optional, defaults to `gpt-4o-mini`)

Example:
```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4o-mini"
uv run python -m chatbot_tui.main
```

### Code Quality

Before committing changes, run the following:

```bash
# Format code with ruff
uv run ruff format src/ tests/

# Check and fix linting issues
uv run ruff check --fix src/ tests/

# Run tests
uv run pytest tests/ -v
```

## Architecture

### Core Components

- **Rich TUI Framework**: Uses Rich's `Console` and live display features for the terminal interface
- **OpenAI SDK Integration**: LLM calls through OpenAI's Python SDK with configurable base URL
- **Message Loop**: Interactive chat loop handling user input and LLM responses

### Design Decisions

- Uses `uv` for fast Python package management and virtual environment handling
- Environment-based configuration for API credentials (never hardcoded)
- Rich library for polished terminal UI with formatting, progress indicators, and panels
