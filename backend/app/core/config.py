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
