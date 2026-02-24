"""LLM client module using OpenAI SDK."""

from openai import AsyncOpenAI, APIError, APITimeoutError
from typing import AsyncGenerator, List, Dict, Any


class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass


class LLMClient:
    """Client for interacting with LLM via OpenAI SDK."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str | None = None,
    ):
        """Initialize the LLM client.

        Args:
            base_url: Base URL for the OpenAI-compatible API
            api_key: API key for authentication
            model: Model name to use
            system_prompt: Optional system prompt to prepend to all messages
        """
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt

    async def chat_stream(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Send a chat message and stream the response.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Yields:
            Content chunks as they arrive from the API

        Raises:
            LLMError: If the API request fails
        """
        # Prepend system prompt if configured
        if self.system_prompt:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *messages,
            ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except APIError as e:
            raise LLMError(f"API error: {e}") from e
        except APITimeoutError as e:
            raise LLMError(f"Request timed out: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e
