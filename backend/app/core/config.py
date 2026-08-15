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
    GEMINI_MODEL: str = "gemini-3.5-flash"

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
