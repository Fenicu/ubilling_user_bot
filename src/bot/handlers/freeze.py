"""Обработчики раздела заморозки."""

import logging
from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards import freeze_confirm_keyboard, freeze_menu_keyboard
from bot.services import BillingService

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "freeze")
async def show_freeze_status(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает статус заморозки аккаунта."""
    try:
        data = await billing.client.get_freeze_data(login, password_md5)
        logger.debug("FreezeData получен: %r", data)
        
        is_frozen = bool(data.freeze_status and data.freeze_status != "0")
        can_freeze = bool(data.freeze_self_available and data.freeze_self_available != "0")

        lines = [
            t("freeze.header"),
            "",
            t("freeze.status", freeze_status=data.freeze_status or t("freeze.not_frozen")),
            t("freeze.price", price=data.user_tariff_freeze_price or "0"),
            t("freeze.period", date_from=data.date_from or "—", date_to=data.date_to or "—"),
            t("freeze.days_used", used=data.freeze_days_used or "0", total=data.freeze_days_total or "0"),
            t("freeze.days_available", available=data.freeze_days_available or "0"),
        ]

        kb = freeze_menu_keyboard(t, can_freeze=can_freeze, is_frozen=is_frozen)
        await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    except Exception:
        logger.exception("Ошибка при обработке данных заморозки")
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=freeze_menu_keyboard(t)
        )
    await callback.answer()


@router.callback_query(F.data == "freeze_action")
async def confirm_freeze(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Запрашивает подтверждение заморозки."""
    await callback.message.edit_text(
        t("freeze.confirm_question"), reply_markup=freeze_confirm_keyboard(t, "freeze")
    )
    await callback.answer()


@router.callback_query(F.data == "unfreeze_action")
async def confirm_unfreeze(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Запрашивает подтверждение разморозки."""
    await callback.message.edit_text(
        t("freeze.unfreeze_question"), reply_markup=freeze_confirm_keyboard(t, "unfreeze")
    )
    await callback.answer()


@router.callback_query(F.data == "freeze_confirm")
async def do_freeze(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Выполняет заморозку аккаунта."""
    try:
        result = await billing.client.freeze_user(login, password_md5)
        logger.debug("Результат заморозки: %r", result)
        text = result.message or t("freeze.frozen")
    except Exception:
        logger.exception("Ошибка при заморозке аккаунта")
        text = t("errors.connection")

    await callback.message.edit_text(text, reply_markup=freeze_menu_keyboard(t))
    await callback.answer()


@router.callback_query(F.data == "unfreeze_confirm")
async def do_unfreeze(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Выполняет разморозку аккаунта."""
    try:
        result = await billing.client.unfreeze_user(login, password_md5)
        logger.debug("Результат разморозки: %r", result)
        text = result.message or t("freeze.unfrozen")
    except Exception:
        logger.exception("Ошибка при разморозке аккаунта")
        text = t("errors.connection")

    await callback.message.edit_text(text, reply_markup=freeze_menu_keyboard(t))
    await callback.answer()
