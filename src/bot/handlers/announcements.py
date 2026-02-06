"""Обработчики раздела объявлений."""

from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button
from bot.services import BillingService

router = Router()


@router.callback_query(F.data == "announcements")
async def show_announcements(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает список объявлений."""
    try:
        announcements = await billing.client.get_announcements(login, password_md5)
    except Exception:
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "menu")]])
        await callback.message.edit_text(t("errors.connection"), reply_markup=kb)
        await callback.answer()
        return

    if not announcements:
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "menu")]])
        await callback.message.edit_text(t("announcements.empty"), reply_markup=kb)
        await callback.answer()
        return

    lines = [t("announcements.header"), ""]
    for ann in announcements[:5]:
        lines.append(f"📢 {ann.title or '—'}")
        lines.append(f"{ann.text or ''}")
        lines.append("───")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("announcements.mark_read"), callback_data="mark_announcements_read")],
            [back_button(t, "menu")],
        ]
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "mark_announcements_read")
async def mark_announcements_read(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Отмечает все объявления прочитанными."""
    try:
        await billing.client.mark_announcements_read(login, password_md5)
        text = t("announcements.marked")
    except Exception:
        text = t("errors.connection")

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "menu")]])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
