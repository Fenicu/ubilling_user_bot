"""Обработчики стороны оператора чата поддержки (support-группа/топик)."""

import logging
from functools import partial
from typing import Callable, Coroutine

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import SupportDialog, async_session
from bot.i18n import LocaleService
from bot.services.reactions import StatusReactions
from bot.services.support import (
    close_dialog,
    find_by_group_message,
    mark_answered,
    record_message,
    touch_dialog,
    unanswered_inbound,
    user_locale,
)
from bot.utils.pagination import parse_page_callback
from bot.utils.support import extract_custom_emoji_ids

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.id == settings.support_chat_id)
router.callback_query.filter(F.message.chat.id == settings.support_chat_id)
if settings.support_topic_id is not None:
    router.message.filter(F.message_thread_id == settings.support_topic_id)

# Дублирует whitelist из support_user.py: разные стороны диалога, свои допущения на будущее.
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


async def _rollback_quietly(db: AsyncSession) -> None:
    """Откатывает сессию после сбоя записи; сбой самого rollback только логируем."""
    try:
        await db.rollback()
    except Exception:
        logger.warning(
            "support_group: не удалось откатить сессию после сбоя записи", exc_info=True
        )


async def _write_or_rollback(
    coro: Coroutine, db: AsyncSession, error_msg: str, *args: object
) -> None:
    """
    Выполняет мутирующий вызов сервиса после уже совершённого действия в Telegram.

    Сбой — rollback сессии (иначе следующий запрос на ней падает с PendingRollbackError,
    маскируя причину) + error-лог. Абоненту/оператору сбой записи не показываем —
    операция в Telegram (доставка/пометка) к этому моменту уже прошла успешно.
    """
    try:
        await coro
    except Exception:
        await _rollback_quietly(db)
        logger.error(error_msg, *args, exc_info=True)


async def _close_as_operator(
    bot: Bot,
    db: AsyncSession,
    dialog: SupportDialog,
    locale_service: LocaleService,
) -> bool:
    """
    Закрывает диалог от лица оператора и приводит его следы в порядок.

    Общий путь для /close и callback sup_close: обновляет статус (True — закрыли мы,
    False — уже был закрыт кем-то ещё), при успехе уведомляет абонента на его локали,
    и в любом случае убирает кнопку «Закрыть» с карточки, если она была отправлена
    (ошибки редактирования — best-effort, только в лог).
    """
    closed = await close_dialog(db, dialog.id, closed_by="operator")

    if closed:
        try:
            locale = await user_locale(db, dialog.telegram_id)
            t_user = partial(locale_service.get, locale)
            await bot.send_message(
                dialog.telegram_id, t_user("support.closed_by_operator")
            )
        except Exception:
            # Сбой SELECT локали мог оставить сессию невалидной — откатываем на всякий случай.
            await _rollback_quietly(db)
            logger.exception(
                "support_group: не удалось уведомить абонента %s о закрытии диалога %s",
                dialog.telegram_id,
                dialog.id,
            )

    if dialog.card_message_id is not None:
        try:
            await bot.edit_message_reply_markup(
                chat_id=settings.support_chat_id,
                message_id=dialog.card_message_id,
                reply_markup=None,
            )
        except Exception:
            logger.warning(
                "support_group: не удалось убрать кнопку с карточки диалога %s",
                dialog.id,
                exc_info=True,
            )

    return closed


@router.message(Command("emoji_id"))
async def cmd_emoji_id(message: Message, t: Callable[..., str], **kwargs) -> None:
    """Показывает custom_emoji_id эмодзи из reply-сообщения — для настройки реакций."""
    reply = message.reply_to_message
    if reply is None:
        await message.reply(t("support_group.emoji_id_hint"))
        return

    pairs = extract_custom_emoji_ids(
        reply.text, reply.entities, reply.caption, reply.caption_entities
    )
    if not pairs:
        await message.reply(t("support_group.emoji_id_hint"))
        return

    lines = [f"{emoji} → <code>{emoji_id}</code>" for emoji, emoji_id in pairs]
    await message.reply("\n".join(lines))


@router.message(Command("close"))
async def cmd_close(
    message: Message,
    t: Callable[..., str],
    locale_service: LocaleService,
    reactions: StatusReactions,
    **kwargs,
) -> None:
    """Закрывает диалог по reply на любое сообщение из его переписки в топике."""
    reply = message.reply_to_message
    if reply is None:
        await message.reply(t("support_group.unknown_reply"))
        return

    async with async_session() as db:
        found = await find_by_group_message(db, reply.message_id)
        if found is None:
            await message.reply(t("support_group.unknown_reply"))
            return

        _, dialog = found
        closed = await _close_as_operator(message.bot, db, dialog, locale_service)

    if closed:
        await reactions.set(settings.support_chat_id, message.message_id, "answered")
        await message.reply(t("support_group.closed_ok"))
    else:
        await message.reply(t("support_group.already_closed"))


@router.callback_query(F.data.startswith("sup_close:"))
async def cb_sup_close(
    callback: CallbackQuery,
    t: Callable[..., str],
    locale_service: LocaleService,
    **kwargs,
) -> None:
    """Закрывает диалог по кнопке «Закрыть диалог» на карточке абонента."""
    dialog_id = parse_page_callback(callback.data)
    if dialog_id is None:
        await callback.answer()
        return

    async with async_session() as db:
        dialog = await db.get(SupportDialog, dialog_id)
        if dialog is None:
            await callback.answer()
            return

        closed = await _close_as_operator(callback.bot, db, dialog, locale_service)
        card_message_id = dialog.card_message_id

    result_text = (
        t("support_group.closed_ok") if closed else t("support_group.already_closed")
    )
    await callback.answer(result_text)
    try:
        await callback.bot.send_message(
            chat_id=settings.support_chat_id,
            message_thread_id=settings.support_topic_id,
            text=result_text,
            reply_to_message_id=card_message_id,
        )
    except Exception:
        logger.exception(
            "support_group: не удалось отправить нотис о закрытии диалога %s из карточки",
            dialog_id,
        )


@router.message(F.reply_to_message)
async def relay_operator_message(
    message: Message,
    t: Callable[..., str],
    reactions: StatusReactions,
    **kwargs,
) -> None:
    """
    Пересылает ответ оператора (reply на сообщение диалога в топике) абоненту.

    Неизвестный reply игнорируется молча — это может быть обычное обсуждение
    в топике, не адресованное конкретному диалогу.
    """
    reply = message.reply_to_message

    async with async_session() as db:
        found = await find_by_group_message(db, reply.message_id)
        if found is None:
            return

        _, dialog = found

        if message.content_type not in SUPPORTED_CONTENT_TYPES:
            await message.reply(t("support_group.unsupported_type"))
            return

        try:
            result = await message.bot.copy_message(
                chat_id=dialog.telegram_id,
                from_chat_id=settings.support_chat_id,
                message_id=message.message_id,
            )
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            await _write_or_rollback(
                record_message(
                    db,
                    dialog.id,
                    message.message_id,
                    "outbound",
                    delivery_status="failed",
                ),
                db,
                "support_group: сбой записи статуса failed для сообщения %s",
                message.message_id,
            )
            await reactions.set(
                settings.support_chat_id, message.message_id, "undelivered"
            )
            await message.reply(t("support_group.undelivered", reason=str(exc)))
            return

        await _write_or_rollback(
            record_message(
                db,
                dialog.id,
                message.message_id,
                "outbound",
                user_message_id=result.message_id,
                delivery_status="delivered",
            ),
            db,
            "support_group: сбой записи в БД после доставки ответа оператора %s абоненту",
            message.message_id,
        )
        await _write_or_rollback(
            touch_dialog(db, dialog.id),
            db,
            "support_group: сбой обновления last_activity_at диалога %s",
            dialog.id,
        )

        batch = await unanswered_inbound(
            db, dialog.id, up_to_group_message_id=reply.message_id
        )
        if batch:
            await _write_or_rollback(
                mark_answered(db, [m.id for m in batch]),
                db,
                "support_group: сбой отметки отвеченных сообщений диалога %s",
                dialog.id,
            )

            for inbound in batch:
                delivered = await reactions.set(
                    settings.support_chat_id, inbound.group_message_id, "answered"
                )
                if not delivered:
                    break

        if dialog.status == "closed":
            await message.reply(t("support_group.delivered_closed"))
