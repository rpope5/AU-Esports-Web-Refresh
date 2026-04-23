"""Add multi-game announcement associations and general tagging.

Revision ID: e1b0f67c9d2a
Revises: 9c5f8f2b7a11
Create Date: 2026-04-23 09:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1b0f67c9d2a"
down_revision: Union[str, Sequence[str], None] = "9c5f8f2b7a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in set(inspector.get_table_names()):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in set(inspector.get_table_names()):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "esports_announcements") and not _column_exists(bind, "esports_announcements", "is_general"):
        with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("is_general", sa.Boolean(), nullable=False, server_default=sa.false())
            )

    if _table_exists(bind, "esports_announcements") and _column_exists(bind, "esports_announcements", "is_general"):
        op.execute(
            sa.text(
                "UPDATE esports_announcements SET is_general = FALSE WHERE is_general IS NULL"
            )
        )

    if (
        _table_exists(bind, "esports_announcements")
        and _table_exists(bind, "games")
        and not _table_exists(bind, "announcement_games")
    ):
        op.create_table(
            "announcement_games",
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("game_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["esports_announcements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("announcement_id", "game_id"),
        )

    if _table_exists(bind, "announcement_games") and not _index_exists(
        bind,
        "announcement_games",
        "ix_announcement_games_game_id",
    ):
        op.create_index("ix_announcement_games_game_id", "announcement_games", ["game_id"], unique=False)

    if (
        _table_exists(bind, "announcement_games")
        and _table_exists(bind, "esports_announcements")
        and _column_exists(bind, "esports_announcements", "game_id")
    ):
        op.execute(
            sa.text(
                """
                INSERT INTO announcement_games (announcement_id, game_id)
                SELECT ea.id, ea.game_id
                FROM esports_announcements ea
                WHERE ea.game_id IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1
                    FROM announcement_games ag
                    WHERE ag.announcement_id = ea.id
                      AND ag.game_id = ea.game_id
                  )
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "announcement_games"):
        if _index_exists(bind, "announcement_games", "ix_announcement_games_game_id"):
            op.drop_index("ix_announcement_games_game_id", table_name="announcement_games")
        op.drop_table("announcement_games")

    if _table_exists(bind, "esports_announcements") and _column_exists(bind, "esports_announcements", "is_general"):
        with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
            batch_op.drop_column("is_general")
