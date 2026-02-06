"""Обработчики авторизации и команды /start."""

import hashlib
import logging
import re
from typing import Callable

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete

from bot.db import Session, async_session
from bot.handlers.menu import show_main_menu
from bot.services import BillingService
from bot.states import AuthForm

logger = logging.getLogger(__name__)

router = Router()

_MD5_RE = re.compile(r"[a-f0-9]{32}")


def _parse_deeplink(payload: str) -> tuple[str, str] | None:
    """Парсит deep link payload формата 'login-md5password'."""
    parts = payload.rsplit("-", 1)
    if len(parts) != 2:
        return None
    login, password_md5 = parts
    if not login or not _MD5_RE.fullmatch(password_md5):
        return None
    return login, password_md5


@router.message(Command("start"))
async def cmd_start(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    command: CommandObject,
    locale: str = "uk",
    **kwargs,
) -> None:
    """Обработка команды /start — deep link, меню или авторизация."""
    # Deep link авторизация: /start login-md5password
    if command.args:
        parsed = _parse_deeplink(command.args)
        if parsed:
            await _handle_deeplink_auth(message, state, t, billing, parsed, locale)
            return

    session = kwargs.get("session")
    if session:
        await state.clear()
        await show_main_menu(message, t, billing, session.login, session.password_md5)
        return

    await state.set_state(AuthForm.waiting_login)
    await message.answer(t("auth.enter_login"))


async def _handle_deeplink_auth(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    credentials: tuple[str, str],
    locale: str,
) -> None:
    """Обрабатывает авторизацию через deep link."""
    login, password_md5 = credentials

    try:
        is_valid = await billing.client.check_auth(login, password_md5)
        if not is_valid:
            logger.warning("Deep link auth failed for login=%s", login)
            await message.answer(t("auth.failed"))
            await state.set_state(AuthForm.waiting_login)
            await message.answer(t("auth.enter_login"))
            return
    except Exception as e:
        logger.exception("Deep link auth error for login=%s: %s", login, e)
        await message.answer(t("errors.connection"))
        await state.set_state(AuthForm.waiting_login)
        await message.answer(t("auth.enter_login"))
        return

    async with async_session() as db:
        session = Session(
            telegram_id=message.from_user.id,
            login=login,
            password_md5=password_md5,
            locale=locale,
        )
        await db.merge(session)
        await db.commit()

    await state.clear()
    await message.answer(t("auth.success"))
    await show_main_menu(message, t, billing, login, password_md5)


@router.message(AuthForm.waiting_login, F.text)
async def process_login(message: Message, state: FSMContext, t: Callable[..., str]) -> None:
    """Обработка ввода логина."""
    await state.update_data(login=message.text)
    await state.set_state(AuthForm.waiting_password)
    await message.answer(t("auth.enter_password"))


@router.message(AuthForm.waiting_password, F.text)
async def process_password(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    bot: Bot,
    billing: BillingService,
    locale: str,
) -> None:
    """Обработка ввода пароля и авторизация."""
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    data = await state.get_data()
    login = data["login"]
    password_md5 = hashlib.md5(message.text.encode()).hexdigest()

    try:
        is_valid = await billing.client.check_auth(login, password_md5)
        logger.debug("check_auth result: %r", is_valid)
        if not is_valid:
            await message.answer(t("auth.failed"))
            await state.set_state(AuthForm.waiting_login)
            await message.answer(t("auth.enter_login"))
            return
    except Exception as e:
        logger.exception("Ошибка при авторизации login=%s: %s", login, e)
        await message.answer(t("errors.connection"))
        await state.set_state(AuthForm.waiting_login)
        await message.answer(t("auth.enter_login"))
        return

    async with async_session() as db:
        session = Session(
            telegram_id=message.from_user.id,
            login=login,
            password_md5=password_md5,
            locale=locale,
        )
        await db.merge(session)
        await db.commit()

    await state.clear()
    await message.answer(t("auth.success"))

    await show_main_menu(message, t, billing, login, password_md5)


@router.message(Command("logout"))
@router.callback_query(F.data == "logout")
async def cmd_logout(
    event: Message | CallbackQuery, state: FSMContext, t: Callable[..., str]
) -> None:
    """Обработка выхода из аккаунта."""
    user_id = event.from_user.id
    async with async_session() as db:
        await db.execute(delete(Session).where(Session.telegram_id == user_id))
        await db.commit()

    await state.clear()
    text = t("auth.logged_out")

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text)
