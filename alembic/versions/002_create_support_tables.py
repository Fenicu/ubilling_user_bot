"""create support chat tables

Revision ID: 002
Revises: 001
Create Date: 2026-07-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_dialogs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("login", sa.String(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.String(10), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("card_message_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("status IN ('open','closed')", name="ck_support_dialogs_status"),
        sa.CheckConstraint("closed_by IN ('operator','user','auto')", name="ck_support_dialogs_closed_by"),
    )
    op.create_index("ix_support_dialogs_telegram_id", "support_dialogs", ["telegram_id"])
    op.create_index("ix_support_dialogs_status_activity", "support_dialogs", ["status", "last_activity_at"])
    op.create_index(
        "uq_support_dialogs_open_per_user",
        "support_dialogs",
        ["telegram_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dialog_id", sa.Integer(), sa.ForeignKey("support_dialogs.id"), nullable=False),
        sa.Column("group_message_id", sa.BigInteger(), nullable=False),
        sa.Column("user_message_id", sa.BigInteger(), nullable=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("answered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("delivery_status", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("direction IN ('inbound','outbound','service')", name="ck_support_messages_direction"),
        sa.CheckConstraint("delivery_status IN ('delivered','failed')", name="ck_support_messages_delivery"),
    )
    op.create_index("ix_support_messages_dialog_id", "support_messages", ["dialog_id"])
    op.create_index("uq_support_messages_group_message_id", "support_messages", ["group_message_id"], unique=True)
    op.create_index("ix_support_messages_batch", "support_messages", ["dialog_id", "direction", "answered"])


def downgrade() -> None:
    op.drop_table("support_messages")
    op.drop_table("support_dialogs")
