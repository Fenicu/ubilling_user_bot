"""Клавиатуры чата поддержки."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def support_chat_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Клавиатура активного диалога с поддержкой: завершить диалог или выйти в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("support.close_btn"), callback_data="sup_user_close")],
            [InlineKeyboardButton(text=t("support.menu_btn_exit"), callback_data="sup_menu_exit")],
        ]
    )


def menu_return_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Клавиатура с одной кнопкой возврата в меню после завершения диалога с поддержкой."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("support.menu_return_btn"), callback_data="sup_menu_exit"
                )
            ],
        ]
    )


def support_card_keyboard(t: Callable[..., str], dialog_id: int) -> InlineKeyboardMarkup:
    """Клавиатура карточки абонента в топике поддержки: закрыть диалог."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("support_group.card_close_btn"),
                    callback_data=f"sup_close:{dialog_id}",
                )
            ]
        ]
    )
