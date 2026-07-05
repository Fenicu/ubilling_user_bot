"""Структурные хелперы извлечения данных из событий aiogram."""

from aiogram.types import Chat, TelegramObject


def get_event_chat(event: TelegramObject) -> Chat | None:
    """
    Возвращает чат события: для Message — message.chat, для CallbackQuery — callback.message.chat.

    Работает структурно (по наличию атрибутов, не через isinstance), поэтому годится
    и для реальных Message/CallbackQuery, и для лёгких стабов в тестах.
    Для CallbackQuery без message (устаревший inline-режим) — None.
    """
    if hasattr(event, "chat"):
        return event.chat
    if hasattr(event, "message"):
        message = event.message
        return message.chat if message is not None else None
    return None
