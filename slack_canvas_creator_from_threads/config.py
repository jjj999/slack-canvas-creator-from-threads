"""Configuration settings for the Slack Canvas Creator app."""

from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Slack settings
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: Optional[str] = None

    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Server settings
    port: int = 3000
    host: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
