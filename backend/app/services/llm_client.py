"""Provider routing for the investigation LLM stages."""

from __future__ import annotations

import logging
from typing import Any, Callable

from app.services.gemini_client import (
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiTransientError,
)

logger = logging.getLogger(__name__)


class FallbackClient:
    """Use one primary provider, then make at most one fallback handoff."""

    def __init__(self, primary: Any, fallback_factory: Callable[[], Any]) -> None:
        self._primary = primary
        self._fallback_factory = fallback_factory

    def generate(self, prompt: str, response_schema: Any = None) -> Any:
        try:
            result = self._primary.generate(prompt, response_schema=response_schema)
            logger.info("provider=gemini outcome=success")
            return result
        except (GeminiRateLimitError, GeminiTimeoutError, GeminiTransientError) as error:
            # The fallback is deliberately outside this try block: a failed Groq
            # request is propagated and can never bounce back to Gemini.
            logger.warning("provider=gemini outcome=unavailable error_type=%s", type(error).__name__)
        fallback = self._fallback_factory()
        logger.info("provider=groq outcome=fallback")
        return fallback.generate(prompt, response_schema=response_schema)
