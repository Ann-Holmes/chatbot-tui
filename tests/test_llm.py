import pytest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletionChunk

from chatbot_tui.llm import LLMClient, LLMError


@pytest.fixture
def mock_stream_response():
    """Create a mock async streaming response."""
    chunks = []

    async def mock_stream():
        for chunk in chunks:
            yield chunk

    mock = Mock()
    mock.chunks = chunks

    async def create(*args, **kwargs):
        return mock_stream()

    mock.create = create
    mock.set_chunks = lambda new_chunks: chunks.__setitem__(slice(None), new_chunks)
    return mock


@pytest.fixture
def llm_client(mock_stream_response):
    """Create LLM client with mocked OpenAI."""
    with patch("chatbot_tui.llm.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions = mock_stream_response
        client = LLMClient(base_url="https://test.com", api_key="test-key")
        client._mock_openai = mock_openai
        client._mock_stream_response = mock_stream_response
        return client


def _create_chunk(content: str | None, finish_reason: str | None = None) -> Mock:
    """Helper to create a mock chat completion chunk."""
    chunk = Mock(spec=ChatCompletionChunk)
    chunk.choices = [Mock()]
    chunk.choices[0].delta.content = content
    chunk.choices[0].finish_reason = finish_reason
    return chunk


class TestLLMClient:
    """Test LLM client initialization and basic operations."""

    def test_init_with_base_url_and_api_key(self, llm_client):
        """Test client initialization with base URL and API key."""
        llm_client._mock_openai.assert_called_once_with(
            base_url="https://test.com", api_key="test-key"
        )

    def test_init_with_system_prompt(self, llm_client):
        """Test client initialization with system prompt."""
        system_prompt = "You are a helpful assistant."
        with patch("chatbot_tui.llm.AsyncOpenAI") as mock_openai:
            mock_openai.return_value.chat.completions = Mock()
            client = LLMClient(
                base_url="https://test.com",
                api_key="test-key",
                system_prompt=system_prompt,
            )
            assert client.system_prompt == system_prompt

    @pytest.mark.asyncio
    async def test_chat_stream_success(self, llm_client):
        """Test successful streaming chat response."""
        llm_client._mock_stream_response.set_chunks(
            [
                _create_chunk("Hello"),
                _create_chunk(" world"),
                _create_chunk("!", finish_reason="stop"),
            ]
        )

        messages = [{"role": "user", "content": "Hi"}]
        full_response = ""
        async for chunk_text in llm_client.chat_stream(messages):
            full_response += chunk_text

        assert full_response == "Hello world!"

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, llm_client):
        """Test that system prompt is included in messages."""
        llm_client.system_prompt = "You are helpful."

        # Track the call args
        call_tracker = {"args": None, "kwargs": None}

        original_create = llm_client._mock_stream_response.create

        async def tracked_create(*args, **kwargs):
            call_tracker["args"] = args
            call_tracker["kwargs"] = kwargs
            return await original_create(*args, **kwargs)

        llm_client._mock_stream_response.create = tracked_create
        llm_client._mock_stream_response.set_chunks(
            [
                _create_chunk("OK", finish_reason="stop"),
            ]
        )

        messages = [{"role": "user", "content": "Hi"}]
        async for _ in llm_client.chat_stream(messages):
            pass

        # Check that system prompt was added
        assert call_tracker["kwargs"] is not None
        sent_messages = call_tracker["kwargs"]["messages"]
        assert sent_messages[0] == {"role": "system", "content": "You are helpful."}
        assert sent_messages[1] == messages[0]

    @pytest.mark.asyncio
    async def test_chat_stream_api_error(self, llm_client):
        """Test API error handling."""
        from openai import APIError

        async def raise_error(*args, **kwargs):
            raise APIError("API Error", request=Mock(), body=Mock())

        llm_client._mock_stream_response.create = raise_error

        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(LLMError, match="API error"):
            async for _ in llm_client.chat_stream(messages):
                pass

    @pytest.mark.asyncio
    async def test_chat_stream_timeout(self, llm_client):
        """Test timeout handling."""
        from openai import APITimeoutError

        async def raise_timeout(*args, **kwargs):
            raise APITimeoutError(request=Mock())

        llm_client._mock_stream_response.create = raise_timeout

        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(LLMError, match="Request timed out"):
            async for _ in llm_client.chat_stream(messages):
                pass

    @pytest.mark.asyncio
    async def test_chat_stream_empty_content(self, llm_client):
        """Test handling of chunks with empty content."""
        llm_client._mock_stream_response.set_chunks(
            [
                _create_chunk(None, finish_reason="stop"),
            ]
        )

        messages = [{"role": "user", "content": "Hi"}]
        full_response = ""
        async for chunk_text in llm_client.chat_stream(messages):
            full_response += chunk_text

        # Should be empty since content was None
        assert full_response == ""

    @pytest.mark.asyncio
    async def test_chat_stream_mixed_content(self, llm_client):
        """Test handling of chunks with mixed content and None."""
        llm_client._mock_stream_response.set_chunks(
            [
                _create_chunk("Hello"),
                _create_chunk(None),  # Should be skipped
                _create_chunk(" World"),
                _create_chunk(""),  # Empty string should be included
                _create_chunk("!", finish_reason="stop"),
            ]
        )

        messages = [{"role": "user", "content": "Hi"}]
        full_response = ""
        async for chunk_text in llm_client.chat_stream(messages):
            full_response += chunk_text

        # Empty string is falsy but should be included
        assert full_response == "Hello World!"
