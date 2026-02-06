"""Клавиатуры раздела платежей."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def payments_menu_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт меню раздела платежей."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("payments.history"), callback_data="payments_history")],
            [InlineKeyboardButton(text=t("payments.fee_history"), callback_data="fee_history")],
            [InlineKeyboardButton(text=t("payments.pay_card"), callback_data="pay_card")],
            [InlineKeyboardButton(text=t("payments.online"), callback_data="payment_systems")],
            [back_button(t, "menu")],
        ]
    )


def fee_period_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора периода для списаний."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("payments.current_month"), callback_data="fee:current")],
            [InlineKeyboardButton(text=t("payments.last_month"), callback_data="fee:last")],
            [InlineKeyboardButton(text=t("payments.three_months"), callback_data="fee:3months")],
            [back_button(t, "payments")],
        ]
    )


def pay_card_cancel_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт кнопку отмены для ввода карты оплаты."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("common.cancel"), callback_data="payments")]]
    )


def payment_systems_keyboard(
    t: Callable[..., str], systems: list[tuple[str, str]]
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру с платёжными системами.

    Args:
        t: Функция перевода
        systems: Список кортежей (название, url)
    """
    buttons = [
        [InlineKeyboardButton(text=f"{name} ↗", url=url)] for name, url in systems
    ]
    buttons.append([back_button(t, "payments")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
