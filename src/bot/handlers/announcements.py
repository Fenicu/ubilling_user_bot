"""Обработчики раздела объявлений."""

import html
from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button, pagination_keyboard
from bot.services import BillingService
from bot.utils.pagination import paginate

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
    """Показывает первую страницу списка объявлений."""
    await _show_announcements_page(callback, t, billing, login, password_md5, 1)


@router.callback_query(F.data.startswith("page:announcements:"))
async def announcements_pagination(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обработка пагинации объявлений."""
    page = int(callback.data.split(":")[2])
    await _show_announcements_page(callback, t, billing, login, password_md5, page)


async def _show_announcements_page(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    page: int,
) -> None:
    """Отображает страницу списка объявлений."""
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

    page_items, total_pages = paginate(announcements, page, page_size=5)
    lines = [t("announcements.header"), ""]
    for ann in page_items:
        lines.append(f"📢 {html.escape(ann.title or '—', quote=False)}")
        lines.append(html.escape(ann.text or "", quote=False))
        lines.append("───")

    mark_read_row = [
        InlineKeyboardButton(
            text=t("announcements.mark_read"), callback_data="mark_announcements_read"
        )
    ]
    kb = pagination_keyboard(
        t, "announcements", page, total_pages, "menu", extra_rows=[mark_read_row]
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
