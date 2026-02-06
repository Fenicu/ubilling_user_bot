"""
Утилиты для безопасного редактирования сообщений Telegram.

Обрабатывает ошибку 'message is not modified', которая возникает
при попытке отредактировать сообщение с тем же содержимым.
"""

from contextlib import contextmanager

from aiogram.exceptions import TelegramBadRequest


def is_message_not_modified(exc: TelegramBadRequest) -> bool:
    """Проверяет, является ли ошибка 'message is not modified'."""
    return "message is not modified" in str(exc)


@contextmanager
def suppress_message_not_modified():
    """
    Контекстный менеджер для игнорирования только ошибки 'message is not modified'.

    Использование:
        with suppress_message_not_modified():
            await message.edit_text(...)
    """
    try:
        yield
    except TelegramBadRequest as exc:
        if not is_message_not_modified(exc):
            raise
