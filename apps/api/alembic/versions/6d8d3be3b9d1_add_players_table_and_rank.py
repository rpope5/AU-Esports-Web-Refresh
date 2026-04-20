"""Add players table and rank field

Revision ID: 6d8d3be3b9d1
Revises: c06176d0720e
Create Date: 2026-04-15 23:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d8d3be3b9d1"
down_revision: Union[str, Sequence[str], None] = "c06176d0720e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "players" not in table_names:
        op.create_table(
            "players",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("gamertag", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("rank", sa.String(), nullable=True),
            sa.Column("game", sa.String(), nullable=False),
            sa.Column("year", sa.String(), nullable=True),
            sa.Column("major", sa.String(), nullable=True),
            sa.Column("headshot", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_players_id"), "players", ["id"], unique=False)
        return

    column_names = {column["name"] for column in inspector.get_columns("players")}
    if "rank" not in column_names:
        with op.batch_alter_table("players", schema=None) as batch_op:
            batch_op.add_column(sa.Column("rank", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "players" not in table_names:
        return

    column_names = {column["name"] for column in inspector.get_columns("players")}
    if "rank" in column_names:
        with op.batch_alter_table("players", schema=None) as batch_op:
            batch_op.drop_column("rank")
