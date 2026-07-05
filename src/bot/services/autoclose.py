"""Фоновый цикл автозакрытия неактивных диалогов чата поддержки."""

import asyncio
import logging
from datetime import UTC, datetime
from functools import partial

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from bot.config import settings
from bot.db import SupportDialog, async_session
from bot.i18n import LocaleService
from bot.services.support import close_dialog, dialogs_to_autoclose, user_locale
from bot.utils.support import autoclose_cutoff

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 3600


async def _autoclose_one(bot: Bot, locale_service: LocaleService, dialog: SupportDialog) -> None:
    """
    Закрывает один диалог и рассылает нотисы.

    close_dialog — conditional UPDATE (WHERE status='open'): если диалог уже закрыт
    оператором/абонентом, closed=False и мы тихо выходим, не перезаписывая чужое закрытие.
    """
    async with async_session() as db:
        closed = await close_dialog(db, dialog.id, closed_by="auto")
        if not closed:
            return
        locale = await user_locale(db, dialog.telegram_id)

    t_user = partial(locale_service.get, locale)
    try:
        await bot.send_message(dialog.telegram_id, t_user("support.autoclosed"))
    except TelegramForbiddenError:
        logger.warning(
            "autoclose: абонент %s заблокировал бота, уведомление о закрытии диалога %s не доставлено",
            dialog.telegram_id,
            dialog.id,
        )

    t_group = partial(locale_service.get, settings.default_locale)
    await bot.send_message(
        chat_id=settings.support_chat_id,
        message_thread_id=settings.support_topic_id,
        text=t_group("support_group.autoclosed_notice"),
        reply_to_message_id=dialog.card_message_id,
    )


async def autoclose_loop(bot: Bot, locale_service: LocaleService) -> None:
    """
    Вечный цикл: раз в час закрывает open-диалоги, неактивные дольше settings.support_autoclose_hours.

    Для каждого: close_dialog(closed_by='auto') → уведомление абоненту (его локаль) —
    TelegramForbiddenError глотаем (лог) → нотис в топик reply'ем на card_message_id.
    Каждый диалог — в своём try/except Exception (одна ошибка не валит цикл).
    Выход — по CancelledError (пробросить).
    """
    logger.info(
        "autoclose: цикл запущен, порог неактивности=%s ч", settings.support_autoclose_hours
    )
    try:
        while True:
            cutoff = autoclose_cutoff(datetime.now(UTC), settings.support_autoclose_hours)
            async with async_session() as db:
                dialogs = await dialogs_to_autoclose(db, cutoff)

            for dialog in dialogs:
                try:
                    await _autoclose_one(bot, locale_service, dialog)
                except Exception:
                    logger.exception("autoclose: сбой автозакрытия диалога %s", dialog.id)

            await asyncio.sleep(_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("autoclose: цикл остановлен")
        raise
