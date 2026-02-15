"""Application configuration using Pydantic Settings.

Loads environment variables and validates configuration for DeepDiver.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from pydantic import SecretStr
from supabase import Client, create_client

# Load .env file early to ensure environment variables are available
from dotenv import load_dotenv

load_dotenv()


# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client.

    Returns:
        Supabase client instance, or None if not configured
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    # Try to get from settings
    try:
        settings = get_settings()
        url = settings.supabase_url
        key = settings.supabase_key.get_secret_value()

        if url and key:
            _supabase_client = create_client(url, key)
            return _supabase_client
    except Exception:
        pass

    return None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str = Field(description="Supabase project URL")
    supabase_key: SecretStr = Field(description="Supabase service role key")
    supabase_anon_key: SecretStr = Field(
        description="Supabase anonymous key for frontend"
    )

    # Market Data APIs
    alpaca_api_key: str = Field(description="Alpaca API key")
    alpaca_secret_key: SecretStr = Field(description="Alpaca secret key")
    finnhub_api_key: str = Field(description="Finnhub API key")

    # OpenRouter (LLM)
    openrouter_api_key: SecretStr = Field(
        description="OpenRouter API key for LLM access"
    )
    openrouter_api_base: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter API base URL"
    )
    openrouter_llm_model: str = Field(
        default="openrouter/minimax/minimax-m2",
        description="Model to use with Google ADK via LiteLLm",
    )

    # App Config
    flask_app: str = Field(default="run.py", description="Flask app entry point")
    port: int = Field(default=8080, description="Server port")
    flask_env: str = Field(default="development", description="Flask environment")

    @model_validator(mode="after")
    def set_litellm_env_vars(self) -> "Settings":
        """Set LiteLLM environment variables after model initialization.

        Returns:
            The Settings instance with environment variables set
        """
        # Set OpenRouter configuration
        os.environ["OPENROUTER_API_KEY"] = self.openrouter_api_key.get_secret_value()
        os.environ["OPENROUTER_API_BASE"] = self.openrouter_api_base

        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings singleton
    """
    return Settings()
