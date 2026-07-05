"""Тесты статусных реакций чата поддержки."""

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import ReactionTypeCustomEmoji, ReactionTypeEmoji

from bot.services.reactions import StatusReactions, resolve_reaction


class FakeBot:
    """Стаб: собирает вызовы set_message_reaction, кидает заданные исключения."""

    def __init__(self, fail_first_with: Exception | None = None):
        self.calls: list[tuple[int, int, object]] = []
        self._fail_first_with = fail_first_with

    async def set_message_reaction(self, chat_id, message_id, reaction):
        if self._fail_first_with is not None:
            exc, self._fail_first_with = self._fail_first_with, None
            self.calls.append((chat_id, message_id, "RAISED"))
            raise exc
        self.calls.append((chat_id, message_id, reaction))


def test_resolve_reaction_standard_emoji():
    """Обычный emoji-символ → ReactionTypeEmoji с этим же значением."""
    result = resolve_reaction("👀")
    assert isinstance(result, ReactionTypeEmoji)
    assert result.emoji == "👀"


def test_resolve_reaction_custom_id():
    """Цифровая строка → ReactionTypeCustomEmoji с этим custom_emoji_id."""
    result = resolve_reaction("5368324170671202286")
    assert isinstance(result, ReactionTypeCustomEmoji)
    assert result.custom_emoji_id == "5368324170671202286"


@pytest.mark.asyncio
async def test_set_uses_configured_reaction():
    """Настроенная реакция ставится успешно с первой попытки."""
    bot = FakeBot()
    config = {"unanswered": "👀", "answered": "👌", "undelivered": "💔"}
    service = StatusReactions(bot, config)

    result = await service.set(chat_id=1, message_id=2, role="answered")

    assert result is True
    assert len(bot.calls) == 1


@pytest.mark.asyncio
async def test_set_falls_back_on_bad_request():
    """Сбой настроенной реакции — fallback на дефолт, роль запоминается сбойной."""
    bad_request = TelegramBadRequest(method=object(), message="REACTION_INVALID")
    bot = FakeBot(fail_first_with=bad_request)
    config = {"unanswered": "👀", "answered": "5368324170671202286", "undelivered": "💔"}
    service = StatusReactions(bot, config)

    result = await service.set(chat_id=1, message_id=2, role="answered")

    assert result is True
    assert len(bot.calls) == 2

    result_second = await service.set(chat_id=1, message_id=3, role="answered")

    assert result_second is True
    assert len(bot.calls) == 3


@pytest.mark.asyncio
async def test_set_gives_up_on_retry_after():
    """Flood-контроль на первой попытке — best-effort сдаётся без повторов и ожидания."""
    retry_after = TelegramRetryAfter(method=object(), message="flood", retry_after=5)
    bot = FakeBot(fail_first_with=retry_after)
    config = {"unanswered": "👀", "answered": "👌", "undelivered": "💔"}
    service = StatusReactions(bot, config)

    result = await service.set(chat_id=1, message_id=2, role="answered")

    assert result is False
    assert len(bot.calls) == 1
