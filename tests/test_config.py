"""Тесты конфигурации приложения."""

from bot.config import Settings


def test_session_ttl_hours_default():
    """SESSION_TTL_HOURS не задан — дефолт -1 (бессрочно)."""
    settings = Settings(_env_file=None)
    assert settings.session_ttl_hours == -1


def test_ubilling_uber_key_empty_string_to_none():
    """Пустая строка UBILLING_UBER_KEY преобразуется в None."""
    settings = Settings(
        ubilling_uber_key="",
        _env_file=None,
    )
    assert settings.ubilling_uber_key is None
