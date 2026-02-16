"""Application configuration using Pydantic Settings.

Loads environment variables and validates configuration for DeepDiver.
"""

import os
from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from pydantic import SecretStr

# Load .env file early to ensure environment variables are available
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (local PostgreSQL)
    database_url: str = Field(
        default="postgresql://deepdiver:deepdiver@localhost:5432/deepdiver",
        description="PostgreSQL connection URL"
    )
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="deepdiver", description="Database name")
    db_user: str = Field(default="deepdiver", description="Database user")
    db_password: SecretStr = Field(default="deepdiver", description="Database password")

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

        # Set database URL
        os.environ["DATABASE_URL"] = f"postgresql://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"

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
