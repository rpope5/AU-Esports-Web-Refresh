"""add mario kart tournament experience details

Revision ID: b3f9c1a7d2ef
Revises: c7f4ab9d2e11
Create Date: 2026-04-08 14:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f9c1a7d2ef"
down_revision: Union[str, Sequence[str], None] = "c7f4ab9d2e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recruit_game_profiles", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("tournament_experience_details", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("recruit_game_profiles", schema=None) as batch_op:
        batch_op.drop_column("tournament_experience_details")
