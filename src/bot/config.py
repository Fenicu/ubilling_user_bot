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
    session_ttl_hours: int = -1
    default_locale: str = "uk"
    log_level: str = "INFO"

    support_chat_id: int | None = None
    support_topic_id: int | None = None
    support_reaction_unanswered: str = "👀"
    support_reaction_answered: str = "👌"
    support_reaction_undelivered: str = "💔"
    support_autoclose_hours: int = 48

    @field_validator("ubilling_uber_key", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Преобразует пустую строку в None."""
        if v is None or v.strip() == "":
            return None
        return v

    @field_validator("support_chat_id", "support_topic_id", mode="before")
    @classmethod
    def support_empty_str_to_none(cls, v: object) -> object:
        """Пустая строка в env → None."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @property
    def support_enabled(self) -> bool:
        """Фича чата поддержки включена, если задан чат."""
        return self.support_chat_id is not None


settings = Settings()
