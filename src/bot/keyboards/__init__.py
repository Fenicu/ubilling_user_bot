"""Клавиатуры бота."""

from bot.keyboards.common import back_button, pagination_keyboard
from bot.keyboards.freeze import freeze_confirm_keyboard, freeze_menu_keyboard
from bot.keyboards.language import language_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.payments import (
    fee_period_keyboard,
    pay_card_cancel_keyboard,
    payment_systems_keyboard,
    payments_menu_keyboard,
)
from bot.keyboards.support import (
    menu_return_keyboard,
    support_card_keyboard,
    support_chat_keyboard,
)
from bot.keyboards.tariffs import tariffs_menu_keyboard
from bot.keyboards.tickets import (
    ticket_cancel_keyboard,
    ticket_view_keyboard,
    tickets_list_keyboard,
    tickets_menu_keyboard,
)

__all__ = [
    "back_button",
    "fee_period_keyboard",
    "freeze_confirm_keyboard",
    "freeze_menu_keyboard",
    "language_keyboard",
    "main_menu_keyboard",
    "menu_return_keyboard",
    "pagination_keyboard",
    "pay_card_cancel_keyboard",
    "payment_systems_keyboard",
    "payments_menu_keyboard",
    "support_card_keyboard",
    "support_chat_keyboard",
    "tariffs_menu_keyboard",
    "ticket_cancel_keyboard",
    "ticket_view_keyboard",
    "tickets_list_keyboard",
    "tickets_menu_keyboard",
]
