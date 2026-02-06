"""Главное меню."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру главного меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("menu.balance"), callback_data="payments"),
                InlineKeyboardButton(text=t("menu.tariff"), callback_data="tariffs"),
            ],
            [
                InlineKeyboardButton(text=t("menu.tickets"), callback_data="tickets"),
                InlineKeyboardButton(text=t("menu.announcements"), callback_data="announcements"),
            ],
            [
                InlineKeyboardButton(text=t("menu.freeze"), callback_data="freeze"),
                InlineKeyboardButton(text=t("menu.credit"), callback_data="credit"),
            ],
            [
                InlineKeyboardButton(text=t("menu.info"), callback_data="info"),
                InlineKeyboardButton(text=t("menu.language"), callback_data="language"),
            ],
            [InlineKeyboardButton(text=t("menu.logout"), callback_data="logout")],
        ]
    )
