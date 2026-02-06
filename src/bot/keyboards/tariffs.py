"""Клавиатуры раздела тарифов."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def tariffs_menu_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт меню раздела тарифов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("tariffs.current"), callback_data="tariff_current")],
            [InlineKeyboardButton(text=t("tariffs.available"), callback_data="tariff_available")],
            [InlineKeyboardButton(text=t("tariffs.all"), callback_data="tariff_all")],
            [back_button(t, "menu")],
        ]
    )
