"""add cs2 and fortnite profile fields

Revision ID: c7f4ab9d2e11
Revises: 072837d9b7e8
Create Date: 2026-04-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7f4ab9d2e11"
down_revision: Union[str, Sequence[str], None] = "072837d9b7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recruit_game_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("epic_games_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("fortnite_pr", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("fortnite_kd", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("fortnite_total_kills", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("fortnite_playtime_hours", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("fortnite_wins", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("faceit_level", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("faceit_elo", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cs2_roles", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("prior_team_history", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("recruit_game_profiles", schema=None) as batch_op:
        batch_op.drop_column("prior_team_history")
        batch_op.drop_column("cs2_roles")
        batch_op.drop_column("faceit_elo")
        batch_op.drop_column("faceit_level")
        batch_op.drop_column("fortnite_wins")
        batch_op.drop_column("fortnite_playtime_hours")
        batch_op.drop_column("fortnite_total_kills")
        batch_op.drop_column("fortnite_kd")
        batch_op.drop_column("fortnite_pr")
        batch_op.drop_column("epic_games_name")

