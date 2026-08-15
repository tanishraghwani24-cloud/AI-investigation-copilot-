"""Tests for the centralized Gemini Client skeleton (Mayur — Round 1).

All tests are offline.  The Gemini SDK is mocked so no real API key
or network access is required.

Covers:
- GeminiClient instantiation
- GeminiClientError exception hierarchy
- generate() → raw text (no schema)
- generate() → validated Pydantic model (with schema)
- generate() wraps SDK errors in GeminiClientError
- generate() wraps JSON/validation errors in GeminiClientError
- get_gemini_client() factory function
- Config integration (GEMINI_API_KEY / GEMINI_MODEL)
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.services.gemini_client import (
    GeminiClient,
    GeminiClientError,
    get_gemini_client,
)


# ── Helper schema used by structured-output tests ────────────────────


class _SampleOutput(BaseModel):
    """Tiny model used to test structured response parsing."""

    label: str
    score: float


# ── Exception tests ──────────────────────────────────────────────────


class TestGeminiClientError:
    """Verify the custom exception behaves correctly."""

    def test_is_exception_subclass(self) -> None:
        """GeminiClientError must be a standard Exception."""
        assert issubclass(GeminiClientError, Exception)

    def test_stores_message(self) -> None:
        err = GeminiClientError("something went wrong")
        assert str(err) == "something went wrong"

    def test_stores_original_error(self) -> None:
        original = ValueError("root cause")
        err = GeminiClientError("wrapped", original_error=original)
        assert err.original_error is original

    def test_original_error_defaults_to_none(self) -> None:
        err = GeminiClientError("no cause")
        assert err.original_error is None


# ── Client instantiation tests ───────────────────────────────────────


class TestGeminiClientInit:
    """Verify client construction and SDK configuration."""

    @patch("app.services.gemini_client.genai")
    def test_instantiates_without_error(self, mock_genai: MagicMock) -> None:
        """Client can be constructed with any key/model pair."""
        client = GeminiClient(api_key="test-key", model_name="gemini-test")
        assert client is not None

    @patch("app.services.gemini_client.genai")
    def test_creates_client_with_api_key(self, mock_genai: MagicMock) -> None:
        """genai.Client is instantiated with the provided API key."""
        GeminiClient(api_key="my-key-123", model_name="gemini-test")
        mock_genai.Client.assert_called_once_with(api_key="my-key-123")

    @patch("app.services.gemini_client.genai")
    def test_stores_model_name(self, mock_genai: MagicMock) -> None:
        """The model name is stored for use in generate calls."""
        client = GeminiClient(api_key="k", model_name="gemini-3.5-flash")
        assert client._model_name == "gemini-3.5-flash"


# ── generate() — raw text mode ───────────────────────────────────────


class TestGenerateRawText:
    """generate() without response_schema returns a plain string."""

    @patch("app.services.gemini_client.genai")
    def test_returns_string(self, mock_genai: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "Generated text output"
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="k", model_name="m")
        result = client.generate("Hello")

        assert isinstance(result, str)
        assert result == "Generated text output"

    @patch("app.services.gemini_client.genai")
    def test_passes_prompt_and_model_to_sdk(self, mock_genai: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="k", model_name="gemini-3.5-flash")
        client.generate("Summarise this case")

        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-3.5-flash",
            contents="Summarise this case",
        )


# ── generate() — structured output mode ──────────────────────────────


class TestGenerateStructured:
    """generate() with a response_schema parses and validates the response."""

    @patch("app.services.gemini_client.genai")
    def test_returns_pydantic_model(self, mock_genai: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"label": "fraud", "score": 0.95}'
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="k", model_name="m")
        result = client.generate("Extract", response_schema=_SampleOutput)

        assert isinstance(result, _SampleOutput)
        assert result.label == "fraud"
        assert result.score == 0.95

    @patch("app.services.gemini_client.genai")
    def test_raises_on_invalid_json(self, mock_genai: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "not valid json {{"
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="k", model_name="m")

        with pytest.raises(GeminiClientError, match="Failed to parse"):
            client.generate("Extract", response_schema=_SampleOutput)

    @patch("app.services.gemini_client.genai")
    def test_raises_on_schema_mismatch(self, mock_genai: MagicMock) -> None:
        """Valid JSON that doesn't match the schema raises GeminiClientError."""
        mock_response = MagicMock()
        mock_response.text = '{"wrong_field": true}'
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="k", model_name="m")

        with pytest.raises(GeminiClientError, match="Failed to parse"):
            client.generate("Extract", response_schema=_SampleOutput)


# ── generate() — error wrapping ──────────────────────────────────────


class TestGenerateErrorHandling:
    """SDK errors are wrapped in GeminiClientError."""

    @patch("app.services.gemini_client.genai")
    def test_wraps_sdk_exception(self, mock_genai: MagicMock) -> None:
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.side_effect = RuntimeError(
            "API unreachable"
        )

        client = GeminiClient(api_key="k", model_name="m")

        with pytest.raises(
            GeminiClientError, match="Gemini API call failed"
        ) as exc_info:
            client.generate("fail prompt")

        assert exc_info.value.original_error is not None
        assert isinstance(exc_info.value.original_error, RuntimeError)


# ── Factory function ─────────────────────────────────────────────────


class TestGetGeminiClient:
    """get_gemini_client() factory uses application settings."""

    @patch("app.services.gemini_client.genai")
    @patch("app.services.gemini_client.settings")
    def test_returns_gemini_client_instance(
        self, mock_settings: MagicMock, mock_genai: MagicMock
    ) -> None:
        mock_settings.GEMINI_API_KEY = "env-key-abc"
        mock_settings.GEMINI_MODEL = "gemini-3.5-flash"

        client = get_gemini_client()
        assert isinstance(client, GeminiClient)

    @patch("app.services.gemini_client.genai")
    @patch("app.services.gemini_client.settings")
    def test_passes_settings_to_client(
        self, mock_settings: MagicMock, mock_genai: MagicMock
    ) -> None:
        mock_settings.GEMINI_API_KEY = "key-xyz"
        mock_settings.GEMINI_MODEL = "gemini-pro"

        client = get_gemini_client()

        mock_genai.Client.assert_called_once_with(api_key="key-xyz")
        assert client._model_name == "gemini-pro"


# ── Config integration ───────────────────────────────────────────────


class TestConfigIntegration:
    """Settings class exposes the Gemini fields."""

    def test_settings_has_gemini_api_key(self) -> None:
        """GEMINI_API_KEY field exists on Settings."""
        assert hasattr(Settings, "model_fields")
        assert "GEMINI_API_KEY" in Settings.model_fields

    def test_settings_has_gemini_model(self) -> None:
        """GEMINI_MODEL field exists on Settings."""
        assert "GEMINI_MODEL" in Settings.model_fields

    def test_gemini_model_default(self) -> None:
        """GEMINI_MODEL defaults to gemini-3.5-flash."""
        assert Settings.model_fields["GEMINI_MODEL"].default == "gemini-3.5-flash"

    def test_gemini_api_key_default_empty(self) -> None:
        """GEMINI_API_KEY defaults to empty string (allows tests to run)."""
        assert Settings.model_fields["GEMINI_API_KEY"].default == ""
