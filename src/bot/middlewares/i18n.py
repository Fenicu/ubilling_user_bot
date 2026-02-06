"""Middleware локализации."""

from functools import partial
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from bot.config import settings
from bot.db import Session, async_session
from bot.i18n import LocaleService


class LocaleMiddleware(BaseMiddleware):
    """Middleware для инжекта функции перевода t()."""

    def __init__(self, locale_service: LocaleService) -> None:
        self._locale_service = locale_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Определяет локаль пользователя и добавляет функцию перевода в data.

        Загружает полный объект Session и кэширует его в data["_db_session"],
        чтобы AuthMiddleware мог переиспользовать его без повторного запроса к БД.
        """
        user_locale, db_session = await self._get_user_locale(event)

        if db_session is not None:
            data["_db_session"] = db_session

        data["locale"] = user_locale
        data["t"] = partial(self._locale_service.get, user_locale)
        data["locale_service"] = self._locale_service

        return await handler(event, data)

    async def _get_user_locale(
        self, event: TelegramObject
    ) -> tuple[str, Session | None]:
        """
        Определяет локаль пользователя.

        Порядок приоритетов:
        1. Сохранённая в сессии локаль
        2. Язык из Telegram-профиля (если поддерживается)
        3. Локаль по умолчанию

        Returns:
            Кортеж (код локали, объект Session или None)
        """
        user_id = self._get_user_id(event)
        tg_lang = self._get_telegram_language(event)

        if user_id:
            async with async_session() as db:
                result = await db.execute(
                    select(Session).where(Session.telegram_id == user_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    return session.locale, session

        if tg_lang and tg_lang in self._locale_service.available:
            return tg_lang, None

        return settings.default_locale, None

    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Извлекает telegram_id из события."""
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None

    def _get_telegram_language(self, event: TelegramObject) -> str | None:
        """Извлекает код языка из Telegram-профиля."""
        if isinstance(event, Message) and event.from_user:
            return event.from_user.language_code
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.language_code
        return None
