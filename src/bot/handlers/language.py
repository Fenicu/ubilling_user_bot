"""Обработчики смены языка."""

from typing import Callable

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update

from bot.db import Session, async_session
from bot.handlers.menu import show_main_menu
from bot.i18n import LocaleService
from bot.keyboards import language_keyboard
from bot.services import BillingService

router = Router()


@router.message(Command("lang"))
async def cmd_lang(
    message: Message, t: Callable[..., str], locale_service: LocaleService, **kwargs
) -> None:
    """Команда /lang — выбор языка."""
    locales = locale_service.available_with_flags
    kb = language_keyboard(t, locales)
    await message.answer(t("language.choose"), reply_markup=kb)


@router.callback_query(F.data == "language")
async def show_language_menu(
    callback: CallbackQuery, t: Callable[..., str], locale_service: LocaleService, **kwargs
) -> None:
    """Показывает меню выбора языка."""
    locales = locale_service.available_with_flags
    kb = language_keyboard(t, locales)
    await callback.message.edit_text(t("language.choose"), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language(
    callback: CallbackQuery,
    locale_service: LocaleService,
    **kwargs,
) -> None:
    """Устанавливает выбранный язык и возвращает в главное меню."""
    new_locale = callback.data.split(":")[1]
    user_id = callback.from_user.id

    async with async_session() as db:
        await db.execute(
            update(Session).where(Session.telegram_id == user_id).values(locale=new_locale)
        )
        await db.commit()

    def t(key, **kw):
        return locale_service.get(new_locale, key, **kw)

    billing: BillingService = kwargs.get("billing")
    login: str = kwargs.get("login")
    password_md5: str = kwargs.get("password_md5")

    if billing and login and password_md5:
        await show_main_menu(callback, t, billing, login, password_md5)
    else:
        await callback.message.edit_text(t("language.changed"))
        await callback.answer()
