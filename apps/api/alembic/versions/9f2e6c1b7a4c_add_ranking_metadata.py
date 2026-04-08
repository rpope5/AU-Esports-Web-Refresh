"""add ranking metadata

Revision ID: 9f2e6c1b7a4c
Revises: fcab3fb0cada
Create Date: 2026-04-02 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f2e6c1b7a4c"
down_revision: Union[str, Sequence[str], None] = "fcab3fb0cada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recruit_rankings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "raw_inputs_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "normalized_features_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )
        batch_op.add_column(
            sa.Column("scoring_method", sa.String(), nullable=False, server_default="rules")
        )
        batch_op.add_column(
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.add_column(
            sa.Column(
                "scored_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.create_index(
            "ix_recruit_rankings_application_game_current",
            ["application_id", "game_id", "is_current"],
            unique=False,
        )
        batch_op.create_index(
            "ix_recruit_rankings_game_current_score",
            ["game_id", "is_current", "score"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_recruit_rankings_game_id_games",
            "games",
            ["game_id"],
            ["id"],
        )

    op.create_index(
        "uq_recruit_rankings_current_per_application_game",
        "recruit_rankings",
        ["application_id", "game_id"],
        unique=True,
        sqlite_where=sa.text("is_current = 1"),
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_recruit_rankings_current_per_application_game", table_name="recruit_rankings")

    with op.batch_alter_table("recruit_rankings", schema=None) as batch_op:
        batch_op.drop_constraint("fk_recruit_rankings_game_id_games", type_="foreignkey")
        batch_op.drop_index("ix_recruit_rankings_game_current_score")
        batch_op.drop_index("ix_recruit_rankings_application_game_current")
        batch_op.drop_column("scored_at")
        batch_op.drop_column("is_current")
        batch_op.drop_column("scoring_method")
        batch_op.drop_column("normalized_features_json")
        batch_op.drop_column("raw_inputs_json")
