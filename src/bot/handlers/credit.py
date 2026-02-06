"""Обработчики раздела кредита."""

from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button
from bot.services import BillingService

router = Router()


@router.callback_query(F.data == "credit")
async def show_credit_info(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает информацию о кредите."""
    try:
        data = await billing.client.check_credit(login, password_md5)
    except Exception:
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "menu")]])
        await callback.message.edit_text(t("errors.connection"), reply_markup=kb)
        await callback.answer()
        return

    lines = [
        t("credit.header"),
        "",
        data.full_message or data.message or t("credit.no_info"),
        "",
        t("credit.period", min_day=data.min_day or "—", max_day=data.max_day or "—"),
        t("credit.price", price=data.credit_price or "0", currency=data.currency or "грн"),
    ]

    buttons = []
    if data.status == 1:
        buttons.append(
            [InlineKeyboardButton(text=t("credit.get_btn"), callback_data="credit_get")]
        )
    buttons.append([back_button(t, "menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "credit_get")
async def confirm_credit(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Запрашивает подтверждение получения кредита."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("credit.confirm"), callback_data="credit_confirm"),
                InlineKeyboardButton(text=t("common.cancel"), callback_data="credit"),
            ]
        ]
    )
    await callback.message.edit_text(t("credit.confirm_question"), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "credit_confirm")
async def do_get_credit(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Выполняет получение кредита."""
    try:
        result = await billing.client.get_credit(login, password_md5)
        text = result.message or t("credit.success")
    except Exception:
        text = t("errors.connection")

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "menu")]])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
