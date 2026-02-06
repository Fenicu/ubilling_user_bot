"""Обработчик главного меню."""

import asyncio
from typing import Callable

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import main_menu_keyboard
from bot.services import BillingService
from bot.utils.formatting import format_user_info

router = Router()


def _extract_tariff_name(services: list) -> str | None:
    """Извлекает название тарифа из списка услуг."""
    for s in services:
        if s.is_tariff:
            return s.tariff_name
    return None


async def show_main_menu(
    event: Message | CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
) -> None:
    """Отображает главное меню с информацией о пользователе."""
    try:
        user, services = await asyncio.gather(
            billing.client.get_user_info(login, password_md5),
            billing.client.get_tariff_vservices(login, password_md5),
        )
        tariff_name = _extract_tariff_name(services)
        text = format_user_info(t, user, tariff_name=tariff_name)
    except Exception:
        text = t("errors.connection")

    kb = main_menu_keyboard(t)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


@router.message(Command("menu"))
async def cmd_menu(
    message: Message,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Команда /menu — возврат в главное меню."""
    await show_main_menu(message, t, billing, login, password_md5)


@router.callback_query(F.data == "menu")
async def callback_menu(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Возврат в главное меню по кнопке."""
    await show_main_menu(callback, t, billing, login, password_md5)


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery) -> None:
    """Заглушка для неактивных кнопок (например, номер страницы)."""
    await callback.answer()
