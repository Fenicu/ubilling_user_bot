"""Проставление статусных реакций на сообщения чата поддержки."""

import logging
from typing import Literal

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import ReactionTypeCustomEmoji, ReactionTypeEmoji

logger = logging.getLogger(__name__)

ReactionRole = Literal["unanswered", "answered", "undelivered"]

DEFAULT_REACTIONS: dict[ReactionRole, str] = {
    "unanswered": "👀",
    "answered": "👌",
    "undelivered": "💔",
}


def resolve_reaction(value: str) -> ReactionTypeEmoji | ReactionTypeCustomEmoji:
    """Цифровая строка → ReactionTypeCustomEmoji(custom_emoji_id=value), иначе ReactionTypeEmoji(emoji=value)."""
    if value.isdigit():
        return ReactionTypeCustomEmoji(custom_emoji_id=value)
    return ReactionTypeEmoji(emoji=value)


class StatusReactions:
    """Ставит статусную реакцию роли, с fallback на дефолт при сбое кастомной."""

    def __init__(self, bot: Bot, config: dict[ReactionRole, str]) -> None:
        """
        Инициализация сервиса.

        Args:
            bot: экземпляр aiogram Bot
            config: настроенные реакции по ролям (собирает вызывающий из settings.support_reaction_*)
        """
        self._bot = bot
        self._config = config
        self._broken_roles: set[ReactionRole] = set()

    async def set(self, chat_id: int, message_id: int, role: ReactionRole) -> bool:
        """
        Ставит реакцию роли. True = поставлена (настроенная или fallback), False = не удалось.

        Логика: если роль уже помечена сбойной — сразу дефолт. Иначе пробуем настроенную;
        TelegramBadRequest → warning-лог, роль помечается сбойной (in-memory, до рестарта),
        ставим дефолт роли. TelegramRetryAfter → return False (не ждём: best-effort, пачку
        прерывает вызывающий). Любая ошибка на дефолте → warning, False.
        """
        if role not in self._broken_roles:
            try:
                await self._apply(chat_id, message_id, self._config[role])
                return True
            except TelegramRetryAfter:
                return False
            except TelegramBadRequest:
                logger.warning(
                    "support.reaction fallback: настроенная реакция роли %r отклонена,"
                    " переключаюсь на дефолт",
                    role,
                )
                self._broken_roles.add(role)

        try:
            await self._apply(chat_id, message_id, DEFAULT_REACTIONS[role])
            return True
        except Exception:
            logger.warning(
                "support.reaction fallback: не удалось поставить дефолтную реакцию роли %r",
                role,
            )
            return False

    async def _apply(self, chat_id: int, message_id: int, value: str) -> None:
        """Вызывает Bot.set_message_reaction с одной реакцией, построенной из value."""
        await self._bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[resolve_reaction(value)],
        )
