"""
Centralized application configuration.

All settings are loaded from environment variables (or a local .env file in
development). Nothing here is hardcoded so the same image can be deployed to
different environments purely via config.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Smart Task Manager API"
    environment: str = "development"
    debug: bool = False
    
    # AI Integration
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model_name: str = "gemini/gemini-1.5-flash"

    # n8n Integration
    n8n_webhook_url: str = "http://n8n:5678/webhook/task-events"

    # Database
    database_url: str = (
        "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    )

    # Auth / JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # n8n integration
    n8n_webhook_base_url: str = "http://localhost:5678/webhook"
    n8n_shared_secret: str = "change-me-in-production"

    # AI (Anthropic)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # File storage
    storage_backend: str = "local"  # "local" | "s3"
    local_storage_path: str = "./uploads"
    s3_bucket_name: str = ""
    s3_region: str = ""

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — import and call this, don't instantiate Settings() directly."""
    return Settings()
