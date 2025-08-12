"""Configuration settings for the Slack Canvas Creator app."""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Slack settings (Socket Mode)
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str  # Required for Socket Mode

    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
