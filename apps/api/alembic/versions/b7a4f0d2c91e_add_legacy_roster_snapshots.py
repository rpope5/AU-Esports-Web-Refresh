"""Add legacy roster snapshot tables.

Revision ID: b7a4f0d2c91e
Revises: 12403619f017
Create Date: 2026-04-28 15:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7a4f0d2c91e"
down_revision: Union[str, Sequence[str], None] = "12403619f017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legacy_rosters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("legacy_rosters", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_legacy_rosters_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_legacy_rosters_created_by_admin_id"), ["created_by_admin_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_legacy_rosters_slug"), ["slug"], unique=True)

    op.create_table(
        "legacy_roster_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("legacy_roster_id", sa.Integer(), nullable=False),
        sa.Column("original_player_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("gamertag", sa.String(), nullable=False),
        sa.Column("game", sa.String(), nullable=False),
        sa.Column("primary_game_slug", sa.String(), nullable=True),
        sa.Column("primary_game_name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("rank", sa.String(), nullable=True),
        sa.Column("year", sa.String(), nullable=True),
        sa.Column("major", sa.String(), nullable=True),
        sa.Column("headshot", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["legacy_roster_id"], ["legacy_rosters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_player_id"], ["players.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("legacy_roster_players", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_legacy_roster_players_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_legacy_roster_players_legacy_roster_id"), ["legacy_roster_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_legacy_roster_players_original_player_id"), ["original_player_id"], unique=False)

    op.create_table(
        "legacy_roster_player_game_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("legacy_roster_player_id", sa.Integer(), nullable=False),
        sa.Column("original_game_id", sa.Integer(), nullable=True),
        sa.Column("game_slug", sa.String(), nullable=False),
        sa.Column("game_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("rank", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["legacy_roster_player_id"], ["legacy_roster_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_game_id"], ["games.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "legacy_roster_player_id",
            "game_slug",
            name="uq_legacy_roster_player_game_profiles_player_slug",
        ),
    )
    with op.batch_alter_table("legacy_roster_player_game_profiles", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_legacy_roster_player_game_profiles_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_legacy_roster_player_game_profiles_legacy_roster_player_id"),
            ["legacy_roster_player_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_legacy_roster_player_game_profiles_original_game_id"),
            ["original_game_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("legacy_roster_player_game_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_roster_player_game_profiles_original_game_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_roster_player_game_profiles_legacy_roster_player_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_roster_player_game_profiles_id"))
    op.drop_table("legacy_roster_player_game_profiles")

    with op.batch_alter_table("legacy_roster_players", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_roster_players_original_player_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_roster_players_legacy_roster_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_roster_players_id"))
    op.drop_table("legacy_roster_players")

    with op.batch_alter_table("legacy_rosters", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_rosters_slug"))
        batch_op.drop_index(batch_op.f("ix_legacy_rosters_created_by_admin_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_rosters_id"))
    op.drop_table("legacy_rosters")
