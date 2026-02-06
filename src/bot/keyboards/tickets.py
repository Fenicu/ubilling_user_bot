"""Клавиатуры раздела тикетов."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def tickets_menu_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт меню раздела тикетов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("tickets.my_tickets"), callback_data="tickets_list")],
            [InlineKeyboardButton(text=t("tickets.create"), callback_data="ticket_create")],
            [back_button(t, "menu")],
        ]
    )


def ticket_reply_keyboard(t: Callable[..., str], ticket_id: int) -> InlineKeyboardMarkup:
    """Создаёт кнопку ответа на тикет."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("tickets.reply", ticket_id=ticket_id),
                    callback_data=f"ticket_reply:{ticket_id}",
                )
            ],
            [back_button(t, "tickets")],
        ]
    )


def ticket_cancel_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт кнопку отмены для создания/ответа на тикет."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("common.cancel"), callback_data="tickets")]]
    )
