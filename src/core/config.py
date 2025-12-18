from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application settings, loaded from environment variables and .env file.
    Defines configurations for API keys, service URLs, server behavior, and prompts.
    Args:
        BaseSettings (_type_): Base class for settings management.
    """

    # --- Server Configuration (for Uvicorn) ---
    APP_HOST: str = Field("localhost", validation_alias="APP_HOST")
    APP_PORT: int = Field(8000, validation_alias="APP_PORT")
    DEBUG_MODE: bool = Field(
        False, validation_alias="DEBUG_MODE"
    )  # For Uvicorn reload and verbose logging
    LOG_LEVEL: str = Field(
        "INFO", validation_alias="LOG_LEVEL"
    )  # e.g., DEBUG, INFO, WARNING, ERROR

    # --- Supabase Configuration ---
    SUPABASE_URL: str = Field(..., validation_alias="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., validation_alias="SUPABASE_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from .env rather than raising an error
        case_sensitive=False,  # Environment variables are often uppercase
    )


config = Config()  # type: ignore
