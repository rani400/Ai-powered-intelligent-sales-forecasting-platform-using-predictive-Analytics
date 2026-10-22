"""Application configuration loaded from environment variables.

All runtime settings are externalised so that no credential or environment-specific value is
hard-coded in the source tree. Values are read from the process environment and from a `.env`
file at the project root when present.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> backend/app -> backend -> <project root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def _split_csv(raw: str) -> list[str]:
    """Split a comma-separated environment value into a clean list."""
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Runtime settings for the SalesGenie AI backend."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "SalesGenie AI")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.api_prefix: str = os.getenv("API_PREFIX", "/api")
        self.debug: bool = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes"}

        self.database_url: str = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{(PROJECT_ROOT / 'salesgenie.db').as_posix()}",
        )
        self.sqlite_foreign_keys: bool = os.getenv(
            "SQLITE_FOREIGN_KEYS", "true"
        ).strip().lower() in {"1", "true", "yes"}

        self.cors_origins: list[str] = _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
        )

        self.llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
        self.llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))

    @property
    def is_sqlite(self) -> bool:
        """True when the configured database is a local SQLite file."""
        return self.database_url.startswith("sqlite")

    @property
    def llm_configured(self) -> bool:
        """True when an LLM provider key is available."""
        return bool(self.llm_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()


settings = get_settings()
