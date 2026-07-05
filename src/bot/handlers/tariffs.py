"""Обработчики раздела тарифов."""

import html
from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.keyboards import tariffs_menu_keyboard
from bot.keyboards.common import back_button, pagination_keyboard
from bot.services import BillingService
from bot.utils.pagination import paginate

router = Router()


@router.callback_query(F.data == "tariffs")
async def show_tariffs_menu(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Отображает меню раздела тарифов."""
    await callback.message.edit_text(t("tariffs.title"), reply_markup=tariffs_menu_keyboard(t))
    await callback.answer()


@router.callback_query(F.data == "tariff_current")
async def show_current_tariff(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает текущий тариф и услуги."""
    try:
        services = await billing.client.get_tariff_vservices(login, password_md5)
    except Exception:
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=tariffs_menu_keyboard(t)
        )
        await callback.answer()
        return

    tariffs = [s for s in services if s.is_tariff]
    vservices = [s for s in services if not s.is_tariff]

    lines = [t("tariffs.current_header"), ""]
    for tariff in tariffs:
        lines.append(t("tariffs.tariff_line", name=tariff.tariff_name, price=tariff.tariff_price, days=tariff.tariff_days_period))

    if vservices:
        lines.append("")
        lines.append(t("tariffs.vservices_header"))
        for vs in vservices:
            lines.append(t("tariffs.vservice_line", name=vs.vservice_name, price=vs.vservice_price, days=vs.vservice_days_period))

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "tariffs")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "tariff_available")
async def show_available_tariffs(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает доступные для смены тарифы."""
    try:
        tariffs = await billing.client.get_allowed_tariffs(login, password_md5)
    except Exception:
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=tariffs_menu_keyboard(t)
        )
        await callback.answer()
        return

    if not tariffs:
        await callback.message.edit_text(
            t("tariffs.no_available"), reply_markup=tariffs_menu_keyboard(t)
        )
        await callback.answer()
        return

    lines = [t("tariffs.available_header"), ""]
    for tariff in tariffs:
        lines.append(f"• {html.escape(tariff.tariff_name, quote=False)}")

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "tariffs")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "tariff_all")
async def show_all_tariffs(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает первую страницу всех тарифов провайдера."""
    await _show_tariff_all_page(callback, t, billing, login, password_md5, 1)


@router.callback_query(F.data.startswith("page:tariff_all:"))
async def tariff_all_pagination(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обработка пагинации списка всех тарифов."""
    page = int(callback.data.split(":")[2])
    await _show_tariff_all_page(callback, t, billing, login, password_md5, page)


async def _show_tariff_all_page(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    page: int,
) -> None:
    """Отображает страницу списка всех тарифов."""
    try:
        services = await billing.client.get_active_tariffs_vservices(login, password_md5)
    except Exception:
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=tariffs_menu_keyboard(t)
        )
        await callback.answer()
        return

    tariffs = [s for s in services if s.is_tariff]
    page_items, total_pages = paginate(tariffs, page)
    lines = [t("tariffs.all_header"), ""]
    for tariff in page_items:
        lines.append(t("tariffs.tariff_line", name=tariff.tariff_name, price=tariff.tariff_price, days=tariff.tariff_days_period))

    kb = pagination_keyboard(t, "tariff_all", page, total_pages, "tariffs")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()
