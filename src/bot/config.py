"""Конфигурация приложения через pydantic-settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота из переменных окружения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    ubilling_url: str
    ubilling_uber_key: str | None = None
    session_ttl_hours: int = 24
    default_locale: str = "uk"
    log_level: str = "INFO"

    @field_validator("ubilling_uber_key", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Преобразует пустую строку в None."""
        if v is None or v.strip() == "":
            return None
        return v


settings = Settings()
