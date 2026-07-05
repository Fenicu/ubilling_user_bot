"""SQLAlchemy модели."""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


class Session(Base):
    """Модель сессии авторизации пользователя."""

    __tablename__ = "sessions"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    login: Mapped[str] = mapped_column(String, nullable=False)
    password_md5: Mapped[str] = mapped_column(String(32), nullable=False)
    locale: Mapped[str] = mapped_column(String(5), nullable=False, default="uk")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SupportDialog(Base):
    """Диалог абонента со службой поддержки."""

    __tablename__ = "support_dialogs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    login: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    card_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class SupportMessage(Base):
    """Маппинг сообщений support-группы на диалоги."""

    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dialog_id: Mapped[int] = mapped_column(
        ForeignKey("support_dialogs.id"), nullable=False, index=True
    )
    group_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    user_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    answered: Mapped[bool] = mapped_column(nullable=False, default=False)
    delivery_status: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
