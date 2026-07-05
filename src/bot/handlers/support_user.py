"""Обработчики абонентской стороны чата поддержки."""

import asyncio
import html
import logging
from functools import partial
from typing import Callable, Coroutine

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import async_session
from bot.handlers.menu import show_main_menu
from bot.i18n import LocaleService
from bot.keyboards.support import support_card_keyboard, support_chat_keyboard
from bot.services import BillingService
from bot.services.reactions import StatusReactions
from bot.services.support import (
    close_dialog,
    find_open_dialog,
    get_or_create_open_dialog,
    record_message,
    set_card_message,
    touch_dialog,
)
from bot.states import SupportForm
from bot.utils.support import build_relay_header, build_subscriber_card

logger = logging.getLogger(__name__)

router = Router()
catchall_router = Router()

SUPPORTED_CONTENT_TYPES = frozenset(
    {
        ContentType.TEXT,
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.DOCUMENT,
        ContentType.VOICE,
        ContentType.VIDEO_NOTE,
        ContentType.AUDIO,
        ContentType.STICKER,
    }
)


class HasOpenDialog(BaseFilter):
    """Пропускает сообщение, только если у абонента есть открытый диалог."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        async with async_session() as db:
            return await find_open_dialog(db, message.from_user.id) is not None


async def _notify_orphan(bot, t_default: Callable[..., str], reply_to_message_id: int) -> None:
    """Уведомляет топик поддержки о потере связи сообщения с диалогом (абоненту не показываем)."""
    try:
        await bot.send_message(
            chat_id=settings.support_chat_id,
            message_thread_id=settings.support_topic_id,
            text=t_default("support_group.orphan_notice"),
            reply_to_message_id=reply_to_message_id,
        )
    except Exception:
        logger.exception("support: не удалось отправить orphan-нотис в топик поддержки")


async def _rollback_quietly(db: AsyncSession) -> None:
    """Откатывает сессию после сбоя записи; сбой самого rollback только логируем."""
    try:
        await db.rollback()
    except Exception:
        logger.warning("support: не удалось откатить сессию после сбоя записи", exc_info=True)


async def _db_write_or_notify(
    coro: Coroutine,
    db: AsyncSession,
    bot,
    t_default: Callable[..., str],
    group_message_id: int,
) -> None:
    """
    Выполняет мутирующую запись сервиса поддержки после успешной отправки в Telegram.

    При сбое — rollback сессии (иначе последующие вызовы на ней падают с
    PendingRollbackError, маскируя причину), лог error + reply-нотис в топик
    (см. спеку: абоненту сбой записи не показываем, сообщение в группу уже ушло успешно).
    """
    try:
        await coro
    except Exception:
        await _rollback_quietly(db)
        logger.error(
            "support: сбой записи в БД после успешной отправки сообщения %s в топик",
            group_message_id,
            exc_info=True,
        )
        await _notify_orphan(bot, t_default, group_message_id)


@router.message(Command("support"))
async def cmd_support(
    message: Message, state: FSMContext, t: Callable[..., str], **kwargs
) -> None:
    """Команда /support — вход в диалог с поддержкой."""
    await state.set_state(SupportForm.chatting)
    await message.answer(t("support.invite"), reply_markup=support_chat_keyboard(t))


@router.callback_query(F.data == "support")
async def show_support_invite(
    callback: CallbackQuery, state: FSMContext, t: Callable[..., str], **kwargs
) -> None:
    """Кнопка «Поддержка» в главном меню — вход в диалог с поддержкой."""
    await state.set_state(SupportForm.chatting)
    await callback.message.edit_text(t("support.invite"), reply_markup=support_chat_keyboard(t))
    await callback.answer()


@router.callback_query(F.data == "sup_menu_exit")
async def exit_support_to_menu(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Выход из диалога с поддержкой в главное меню (диалог не закрывается)."""
    await state.clear()
    await show_main_menu(callback, t, billing, login, password_md5)


@router.callback_query(F.data == "sup_user_close")
async def close_support_by_user(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[..., str],
    locale_service: LocaleService,
    **kwargs,
) -> None:
    """Закрывает диалог по инициативе абонента."""
    t_default = partial(locale_service.get, settings.default_locale)

    async with async_session() as db:
        dialog = await find_open_dialog(db, callback.from_user.id)
        if dialog is not None:
            await close_dialog(db, dialog.id, closed_by="user")
            try:
                await callback.bot.send_message(
                    chat_id=settings.support_chat_id,
                    message_thread_id=settings.support_topic_id,
                    text=t_default("support_group.closed_by_user"),
                    reply_to_message_id=dialog.card_message_id,
                )
            except Exception:
                logger.exception(
                    "support: не удалось уведомить топик о закрытии диалога %s абонентом",
                    dialog.id,
                )

    await state.clear()
    await callback.message.edit_text(t("support.closed"))
    await callback.answer()


async def relay_message(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    locale_service: LocaleService,
    billing: BillingService,
    login: str,
    password_md5: str,
    reactions: StatusReactions,
    **kwargs,
) -> None:
    """
    Пересылает сообщение абонента в топик поддержки.

    При первом сообщении диалога — создаёт диалог и постит карточку абонента в топик.
    Подтверждение абоненту («сообщение доставлено») отправляется только на первое сообщение,
    дальше пересылка идёт молча.
    """
    if message.content_type not in SUPPORTED_CONTENT_TYPES:
        await message.answer(t("support.unsupported_type"))
        return

    t_default = partial(locale_service.get, settings.default_locale)
    telegram_id = message.from_user.id
    bot = message.bot

    async with async_session() as db:
        dialog, created = await get_or_create_open_dialog(db, telegram_id, login)

        # dialog.card_message_id is None у существующего диалога значит, что предыдущая
        # попытка отправить карточку сорвалась (упала после коммита диалога) — пробуем
        # ещё раз на следующем сообщении, а не оставляем диалог без карточки навсегда.
        # first_ack абоненту — только для по-настоящему нового диалога (created), чтобы
        # не шуметь повторным «Передано оператору» на каждом сообщении без карточки.
        if created or dialog.card_message_id is None:
            try:
                user, services = await asyncio.gather(
                    billing.client.get_user_info(login, password_md5),
                    billing.client.get_tariff_vservices(login, password_md5),
                )
                tariff_name = next((s.tariff_name for s in services if s.is_tariff), None)
            except Exception:
                logger.warning(
                    "support: не удалось получить данные абонента %s для карточки — заглушка",
                    login,
                    exc_info=True,
                )
                user, tariff_name = None, None

            card_text = build_subscriber_card(t_default, login, telegram_id, user, tariff_name)
            try:
                card_msg = await bot.send_message(
                    chat_id=settings.support_chat_id,
                    message_thread_id=settings.support_topic_id,
                    text=card_text,
                    reply_markup=support_card_keyboard(t_default, dialog.id),
                )
            except TelegramAPIError:
                logger.exception("support: не удалось отправить карточку абонента в топик")
                await message.answer(t("support.relay_error"))
                return

            await _db_write_or_notify(
                record_message(db, dialog.id, card_msg.message_id, "service"),
                db,
                bot,
                t_default,
                card_msg.message_id,
            )
            await _db_write_or_notify(
                set_card_message(db, dialog.id, card_msg.message_id),
                db,
                bot,
                t_default,
                card_msg.message_id,
            )

            if created:
                await message.answer(t("support.first_ack"))

        header = build_relay_header(t_default, login, None)

        if message.content_type == ContentType.TEXT:
            text = f"{header}\n\n{html.escape(message.text, quote=False)}"
            try:
                sent = await bot.send_message(
                    chat_id=settings.support_chat_id,
                    message_thread_id=settings.support_topic_id,
                    text=text,
                )
            except TelegramAPIError:
                logger.exception("support: не удалось переслать текст абонента в топик")
                await message.answer(t("support.relay_error"))
                return

            inbound_message_id = sent.message_id
            await _db_write_or_notify(
                record_message(
                    db, dialog.id, inbound_message_id, "inbound", user_message_id=message.message_id
                ),
                db,
                bot,
                t_default,
                inbound_message_id,
            )
        else:
            try:
                header_msg = await bot.send_message(
                    chat_id=settings.support_chat_id,
                    message_thread_id=settings.support_topic_id,
                    text=header,
                )
            except TelegramAPIError:
                logger.exception("support: не удалось отправить шапку медиасообщения в топик")
                await message.answer(t("support.relay_error"))
                return

            await _db_write_or_notify(
                record_message(db, dialog.id, header_msg.message_id, "service"),
                db,
                bot,
                t_default,
                header_msg.message_id,
            )

            try:
                copied = await bot.copy_message(
                    chat_id=settings.support_chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    message_thread_id=settings.support_topic_id,
                )
            except TelegramAPIError:
                logger.exception("support: не удалось скопировать медиа абонента в топик")
                await message.answer(t("support.relay_error"))
                return

            inbound_message_id = copied.message_id
            await _db_write_or_notify(
                record_message(
                    db, dialog.id, inbound_message_id, "inbound", user_message_id=message.message_id
                ),
                db,
                bot,
                t_default,
                inbound_message_id,
            )

        await reactions.set(settings.support_chat_id, inbound_message_id, "unanswered")
        try:
            await touch_dialog(db, dialog.id)
        except Exception:
            # Не потеря маппинга — orphan-нотис не нужен, абоненту сбой не показываем.
            await _rollback_quietly(db)
            logger.error(
                "support: сбой обновления last_activity_at диалога %s", dialog.id, exc_info=True
            )


router.message.register(relay_message, StateFilter(SupportForm.chatting))
catchall_router.message.register(relay_message, StateFilter(None), HasOpenDialog())
