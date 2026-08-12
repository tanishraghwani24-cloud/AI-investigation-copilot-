"""Centralized Gemini Client.

Provides a single reusable GeminiClient class that every future agent will
use to interact with Google's Gemini API.  Round 1 implements the skeleton:
basic configuration, a single ``generate()`` method, and a custom exception.

No retries, no rate limiting, no hardening — those belong to future rounds.
"""

import json
from typing import TypeVar

from google import genai
from pydantic import BaseModel, ValidationError

from app.core.config import settings

# Generic type variable for Pydantic model returns
T = TypeVar("T", bound=BaseModel)


# ============================================================
# Custom Exception
# ============================================================


class GeminiClientError(Exception):
    """Raised when a Gemini API call fails.

    Wraps all SDK and validation errors into a single, predictable
    exception that callers can catch without depending on the
    underlying SDK's exception hierarchy.
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


# ============================================================
# Gemini Client
# ============================================================


class GeminiClient:
    """Reusable client for Google Gemini generative AI.

    Usage::

        client = GeminiClient(api_key="...", model_name="gemini-2.0-flash")
        text = client.generate("Summarise this case.")
        model = client.generate("Extract data.", response_schema=MyModel)

    Args:
        api_key: Google AI API key.
        model_name: Gemini model identifier (e.g. ``"gemini-2.0-flash"``).
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        self._api_key = api_key
        self._model_name = model_name

        # Instantiate the google-genai Client with the API key
        self._client = genai.Client(api_key=self._api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generate content from a text prompt.

        Args:
            prompt: The text prompt to send to Gemini.
            response_schema: If provided, the raw response text is parsed
                and validated into this Pydantic model.  When ``None``,
                the raw text string is returned instead.

        Returns:
            The generated text (``str``) when *response_schema* is ``None``,
            or a validated Pydantic model instance when a schema is given.

        Raises:
            GeminiClientError: On any SDK, network, or validation failure.
        """
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            raw_text: str = response.text
        except Exception as exc:
            raise GeminiClientError(
                f"Gemini API call failed: {exc}",
                original_error=exc,
            ) from exc

        # --- Raw text mode ---
        if response_schema is None:
            return raw_text

        # --- Structured output mode ---
        try:
            parsed_data = json.loads(raw_text)
            return response_schema.model_validate(parsed_data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise GeminiClientError(
                f"Failed to parse Gemini response into {response_schema.__name__}: {exc}",
                original_error=exc,
            ) from exc


# ============================================================
# Factory
# ============================================================


def get_gemini_client() -> GeminiClient:
    """Create a GeminiClient using application settings.

    Reads ``GEMINI_API_KEY`` and ``GEMINI_MODEL`` from the centralised
    ``Settings`` object (environment / ``.env`` file).
    """
    return GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
    )
