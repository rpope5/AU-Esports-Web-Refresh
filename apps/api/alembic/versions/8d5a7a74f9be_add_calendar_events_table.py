"""add calendar events table

Revision ID: 8d5a7a74f9be
Revises: 30e361842e30
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d5a7a74f9be"
down_revision: Union[str, Sequence[str], None] = "30e361842e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("game", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calendar_events_id"), "calendar_events", ["id"], unique=False)
    op.create_index(op.f("ix_calendar_events_time"), "calendar_events", ["time"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_calendar_events_time"), table_name="calendar_events")
    op.drop_index(op.f("ix_calendar_events_id"), table_name="calendar_events")
    op.drop_table("calendar_events")
