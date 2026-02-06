"""Клавиатуры раздела заморозки."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def freeze_menu_keyboard(
    t: Callable[..., str], can_freeze: bool = True, is_frozen: bool = False
) -> InlineKeyboardMarkup:
    """
    Создаёт меню раздела заморозки.

    Args:
        t: Функция перевода
        can_freeze: Доступна ли самозаморозка
        is_frozen: Заморожен ли аккаунт
    """
    buttons: list[list[InlineKeyboardButton]] = []

    if can_freeze and not is_frozen:
        buttons.append(
            [InlineKeyboardButton(text=t("freeze.freeze_btn"), callback_data="freeze_action")]
        )

    if is_frozen:
        buttons.append(
            [InlineKeyboardButton(text=t("freeze.unfreeze_btn"), callback_data="unfreeze_action")]
        )

    buttons.append([back_button(t, "menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def freeze_confirm_keyboard(t: Callable[..., str], action: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру подтверждения заморозки/разморозки.

    Args:
        t: Функция перевода
        action: 'freeze' или 'unfreeze'
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(f"freeze.confirm_{action}"), callback_data=f"{action}_confirm"
                ),
                InlineKeyboardButton(text=t("common.cancel"), callback_data="freeze"),
            ]
        ]
    )
