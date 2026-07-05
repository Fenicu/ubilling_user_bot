"""Тесты конфигурации приложения."""

from bot.config import Settings


def _make_settings(**kw):
    """Создаёт Settings с обязательными полями для теста, без чтения .env."""
    return Settings(
        _env_file=None,
        bot_token="1:t",
        database_url="postgresql+asyncpg://t:t@localhost/t",
        ubilling_url="http://localhost",
        **kw,
    )


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


def test_support_disabled_by_default():
    """Без SUPPORT_CHAT_ID фича выключена."""
    s = _make_settings()
    assert s.support_chat_id is None
    assert s.support_enabled is False


def test_support_chat_id_empty_string_is_none():
    """Пустая строка в env трактуется как None."""
    s = _make_settings(support_chat_id="", support_topic_id="")
    assert s.support_chat_id is None
    assert s.support_topic_id is None


def test_support_enabled_with_chat_id():
    """Заданный SUPPORT_CHAT_ID включает фичу и дефолтные реакции."""
    s = _make_settings(support_chat_id="-1001234567890")
    assert s.support_enabled is True
    assert s.support_reaction_unanswered == "👀"
    assert s.support_reaction_answered == "👌"
    assert s.support_reaction_undelivered == "💔"
    assert s.support_autoclose_hours == 48
