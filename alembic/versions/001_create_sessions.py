"""create sessions table

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("login", sa.String(), nullable=False),
        sa.Column("password_md5", sa.String(32), nullable=False),
        sa.Column("locale", sa.String(5), nullable=False, server_default="uk"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("telegram_id"),
    )


def downgrade() -> None:
    op.drop_table("sessions")
