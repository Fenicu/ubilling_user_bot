"""Клавиатура выбора языка."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def language_keyboard(
    t: Callable[..., str], locales: dict[str, tuple[str, str]]
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру выбора языка.

    Args:
        t: Функция перевода
        locales: Словарь {code: (name, flag)}
    """
    buttons = [
        [InlineKeyboardButton(text=f"{flag} {name}", callback_data=f"set_lang:{code}")]
        for code, (name, flag) in locales.items()
    ]
    buttons.append([back_button(t, "menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
