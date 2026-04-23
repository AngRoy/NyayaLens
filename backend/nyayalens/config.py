"""Application configuration, loaded from environment variables.

Loaded once at startup via `get_settings()`; injected into FastAPI routes via
dependency injection. Never read environment variables directly from services —
always read from `Settings`.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "staging", "prod"]


class Settings(BaseSettings):
    """Top-level app settings.

    Values come from (in precedence order):
      1. Environment variables
      2. `.env` file at the backend root
      3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- Core --
    nyayalens_env: Environment = "dev"
    nyayalens_log_level: str = "INFO"

    # -- Gemini --
    gemini_api_key: str = ""
    gemini_model_explain: str = "gemini-flash-latest"
    gemini_model_schema: str = "gemini-pro-latest"
    gemini_temperature: float = 0.2
    gemini_daily_token_budget_per_org: int = 1_000_000

    # -- Firebase project --
    google_cloud_project: str = ""
    firebase_storage_bucket: str = ""

    # -- Firebase emulators (auto-detected from env) --
    firestore_emulator_host: str = ""
    firebase_auth_emulator_host: str = ""
    firebase_storage_emulator_host: str = ""

    # -- Auth --
    google_application_credentials: str = ""

    # -- Server --
    host: str = "127.0.0.1"
    port: int = 8000
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5000"

    # -- Feature flags --
    enable_response_cache: bool = True
    enable_grounding_validator: bool = True

    # -- Derived --

    @property
    def is_using_emulators(self) -> bool:
        """True when at least one Firebase emulator host is set.

        When this is True the backend uses emulator endpoints and relaxes a
        few auth checks (e.g. does not require real GCP credentials).
        """
        return bool(
            self.firestore_emulator_host
            or self.firebase_auth_emulator_host
            or self.firebase_storage_emulator_host
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.nyayalens_env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Cached so every request reuses the same object. Call
    `get_settings.cache_clear()` in tests that need to alter env vars.
    """
    return Settings()
