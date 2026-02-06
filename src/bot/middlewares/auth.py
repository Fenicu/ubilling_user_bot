"""Middleware авторизации."""

from datetime import UTC, datetime, timedelta
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import delete, select

from bot.config import settings
from bot.db import Session, async_session


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователя."""

    SKIP_COMMANDS = {"/start"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Проверяет наличие активной сессии перед обработкой события.

        При валидной сессии добавляет login, password_md5 и session в data.
        Для /start — пропускает без ошибки, но инжектит сессию если она валидна.
        """
        user_id = self._get_user_id(event)
        if user_id is None:
            return await handler(event, data)

        is_start = self._is_start_command(event)

        state = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state and current_state.startswith("AuthForm:"):
                return await handler(event, data)

        # Переиспользуем сессию из LocaleMiddleware, если доступна
        session = data.pop("_db_session", None)
        if session is None:
            async with async_session() as db:
                result = await db.execute(
                    select(Session).where(Session.telegram_id == user_id)
                )
                session = result.scalar_one_or_none()

        if session is None:
            if is_start:
                return await handler(event, data)
            await self._send_unauthorized(event, data)
            return None

        if settings.session_ttl_hours > 0:
            ttl = timedelta(hours=settings.session_ttl_hours)
            if datetime.now(UTC) - session.created_at.replace(tzinfo=UTC) > ttl:
                async with async_session() as db:
                    await db.execute(
                        delete(Session).where(Session.telegram_id == user_id)
                    )
                    await db.commit()
                if is_start:
                    return await handler(event, data)
                await self._send_session_expired(event, data)
                return None

        data["login"] = session.login
        data["password_md5"] = session.password_md5
        data["session"] = session

        return await handler(event, data)

    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Извлекает telegram_id из события."""
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None

    def _is_start_command(self, event: TelegramObject) -> bool:
        """Проверяет, является ли событие командой /start."""
        if isinstance(event, Message) and event.text:
            return event.text.split()[0] in self.SKIP_COMMANDS
        return False

    async def _send_unauthorized(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> None:
        """Отправляет сообщение о необходимости авторизации."""
        t = data.get("t")
        text = t("auth.session_expired") if t else "Сессия истекла. Нажмите /start"
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)

    async def _send_session_expired(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> None:
        """Отправляет сообщение об истечении сессии."""
        await self._send_unauthorized(event, data)
