"""Async DB-операции чата поддержки: диалоги и сообщения support-группы."""

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import Session, SupportDialog, SupportMessage


async def get_or_create_open_dialog(
    db: AsyncSession, telegram_id: int, login: str
) -> tuple[SupportDialog, bool]:
    """
    Возвращает открытый диалог абонента, создавая его при отсутствии.

    INSERT ... ON CONFLICT DO NOTHING поверх партиального unique-индекса
    (telegram_id WHERE status='open') + повторный SELECT при конфликте —
    закрывает гонку двух почти одновременных сообщений одного абонента.
    """
    stmt = (
        insert(SupportDialog)
        .values(telegram_id=telegram_id, login=login)
        .on_conflict_do_nothing(
            index_elements=["telegram_id"],
            index_where=sa.text("status = 'open'"),
        )
        .returning(SupportDialog.id)
    )
    result = await db.execute(stmt)
    new_id = result.scalar_one_or_none()

    if new_id is not None:
        await db.commit()
        dialog = await db.get(SupportDialog, new_id)
        return dialog, True

    existing = await db.execute(
        select(SupportDialog).where(
            SupportDialog.telegram_id == telegram_id,
            SupportDialog.status == "open",
        )
    )
    return existing.scalar_one(), False


async def close_dialog(db: AsyncSession, dialog_id: int, closed_by: str) -> bool:
    """Закрывает открытый диалог. True — закрыли мы, False — уже был закрыт кем-то ещё."""
    result = await db.execute(
        update(SupportDialog)
        .where(SupportDialog.id == dialog_id, SupportDialog.status == "open")
        .values(status="closed", closed_by=closed_by, closed_at=datetime.now(UTC))
    )
    await db.commit()
    return result.rowcount > 0


async def record_message(
    db: AsyncSession,
    dialog_id: int,
    group_message_id: int,
    direction: str,
    user_message_id: int | None = None,
    delivery_status: str | None = None,
) -> None:
    """Сохраняет маппинг сообщения support-группы на диалог."""
    db.add(
        SupportMessage(
            dialog_id=dialog_id,
            group_message_id=group_message_id,
            user_message_id=user_message_id,
            direction=direction,
            delivery_status=delivery_status,
        )
    )
    await db.commit()


async def find_by_group_message(
    db: AsyncSession, group_message_id: int
) -> tuple[SupportMessage, SupportDialog] | None:
    """Находит сообщение и его диалог по id сообщения в support-группе."""
    result = await db.execute(
        select(SupportMessage, SupportDialog)
        .join(SupportDialog, SupportMessage.dialog_id == SupportDialog.id)
        .where(SupportMessage.group_message_id == group_message_id)
    )
    row = result.first()
    return (row[0], row[1]) if row is not None else None


async def unanswered_inbound(
    db: AsyncSession, dialog_id: int, up_to_group_message_id: int | None
) -> list[SupportMessage]:
    """
    Неотвеченные входящие сообщения диалога до указанного (включительно).

    message_id в чате монотонно растёт — group_message_id <= up_to_group_message_id
    и есть «более ранние или это же» сообщения. up_to_group_message_id=None — без
    верхней границы (все неотвеченные inbound диалога): нужно для реплая на карточку
    или шапку медиа — у них нет собственной позиции среди входящих сообщений диалога.
    """
    conditions = [
        SupportMessage.dialog_id == dialog_id,
        SupportMessage.direction == "inbound",
        SupportMessage.answered.is_(False),
    ]
    if up_to_group_message_id is not None:
        conditions.append(SupportMessage.group_message_id <= up_to_group_message_id)

    result = await db.execute(
        select(SupportMessage).where(*conditions).order_by(SupportMessage.created_at)
    )
    return list(result.scalars().all())


async def mark_answered(db: AsyncSession, message_ids: list[int]) -> None:
    """Помечает сообщения отвеченными."""
    if not message_ids:
        return
    await db.execute(
        update(SupportMessage).where(SupportMessage.id.in_(message_ids)).values(answered=True)
    )
    await db.commit()


async def touch_dialog(db: AsyncSession, dialog_id: int) -> None:
    """Обновляет last_activity_at диалога текущим временем."""
    await db.execute(
        update(SupportDialog)
        .where(SupportDialog.id == dialog_id)
        .values(last_activity_at=datetime.now(UTC))
    )
    await db.commit()


async def set_card_message(db: AsyncSession, dialog_id: int, card_message_id: int) -> None:
    """Сохраняет id сообщения-карточки абонента в топике."""
    await db.execute(
        update(SupportDialog)
        .where(SupportDialog.id == dialog_id)
        .values(card_message_id=card_message_id)
    )
    await db.commit()


async def find_open_dialog(db: AsyncSession, telegram_id: int) -> SupportDialog | None:
    """Возвращает открытый диалог абонента, если есть."""
    result = await db.execute(
        select(SupportDialog).where(
            SupportDialog.telegram_id == telegram_id,
            SupportDialog.status == "open",
        )
    )
    return result.scalar_one_or_none()


async def dialogs_to_autoclose(db: AsyncSession, cutoff: datetime) -> list[SupportDialog]:
    """Открытые диалоги без активности с cutoff — кандидаты на автозакрытие."""
    result = await db.execute(
        select(SupportDialog).where(
            SupportDialog.status == "open",
            SupportDialog.last_activity_at < cutoff,
        )
    )
    return list(result.scalars().all())


async def user_locale(db: AsyncSession, telegram_id: int) -> str:
    """Локаль абонента из sessions; нет сессии → settings.default_locale."""
    result = await db.execute(select(Session.locale).where(Session.telegram_id == telegram_id))
    locale = result.scalar_one_or_none()
    return locale or settings.default_locale
