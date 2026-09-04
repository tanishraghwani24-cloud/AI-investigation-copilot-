from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    Loaded from environment variables and .env file.
    Additional setting groups (database, Gemini, etc.) will be
    added in future phases.
    """

    APP_NAME: str = "AI Investigation Copilot API"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api"

    # --- API authentication ---
    # Shared secret required on protected routes via the X-API-Key header.
    # Minimal hackathon-scoped auth — not a user/session/RBAC system.
    API_SHARED_SECRET: str = ""

    # --- Database (Supabase PostgreSQL) ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/investigation_db"

    # --- Gemini / LLM Settings ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.7-flash"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_BACKOFF_BASE_SECONDS: float = 0.5
    GEMINI_BACKOFF_MAX_SECONDS: float = 8.0
    GEMINI_STRUCTURED_CORRECTION_RETRIES: int = 1
    # Primary/fallback routing. REASONING_LLM_PROVIDER remains supported for
    # existing deployments that explicitly select Ollama.
    LLM_PRIMARY_PROVIDER: str = "gemini"
    LLM_FALLBACK_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT_SECONDS: float = 30.0
    GROQ_MAX_RETRIES: int = 1
    GROQ_BACKOFF_BASE_SECONDS: float = 0.5
    GROQ_BACKOFF_MAX_SECONDS: float = 8.0
    GROQ_STRUCTURED_CORRECTION_RETRIES: int = 1
    # openai/gpt-oss-20b is a reasoning model: chain-of-thought tokens are spent
    # from the same completion budget as the final JSON answer. Its verified
    # ceiling is 65536 completion tokens; 16384 leaves ample headroom over the
    # ~1.5-2.3k a reasoning call actually uses, without masking a runaway.
    GROQ_MAX_COMPLETION_TOKENS: int = 16384
    # The real fix for budget exhaustion is shortening the chain-of-thought
    # rather than enlarging the budget. Hypothesis generation reasons over facts
    # already supplied in the prompt, so "low" is sufficient. Set to "" to let
    # the model use its own default.
    GROQ_REASONING_EFFORT: str = "low"
    # Demo mode swaps the reasoning/compliance/decision LLM for a
    # deterministic offline stand-in so a demo cannot be stalled by provider
    # quota exhaustion. It is opt-in and must stay false in production: when
    # false the Gemini -> Groq path below is used exactly as before.
    DEMO_MODE: bool = False
    # Mock Bank incoming-activity simulator. Generates new transactions and the
    # alerts they trigger so the Officer Inbox behaves like a live queue.
    # Pinned off under tests so a suite never writes simulated rows.
    MOCK_BANK_SIMULATOR_ENABLED: bool = True
    MOCK_BANK_SIMULATOR_MIN_SECONDS: float = 20.0
    MOCK_BANK_SIMULATOR_MAX_SECONDS: float = 30.0
    REASONING_LLM_PROVIDER: str = "gemini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0
    OLLAMA_MAX_RETRIES: int = 1
    OLLAMA_BACKOFF_BASE_SECONDS: float = 0.5
    OLLAMA_BACKOFF_MAX_SECONDS: float = 8.0
    OLLAMA_STRUCTURED_CORRECTION_RETRIES: int = 1

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings: Settings = get_settings()
