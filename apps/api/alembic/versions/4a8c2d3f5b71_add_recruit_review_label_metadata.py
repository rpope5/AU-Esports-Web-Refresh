"""add recruit review label metadata

Revision ID: 4a8c2d3f5b71
Revises: 9f2e6c1b7a4c
Create Date: 2026-04-02 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a8c2d3f5b71"
down_revision: Union[str, Sequence[str], None] = "9f2e6c1b7a4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VALID_STATUSES = (
    "NEW",
    "REVIEWED",
    "CONTACTED",
    "TRYOUT",
    "WATCHLIST",
    "ACCEPTED",
    "REJECTED",
)


def upgrade() -> None:
    op.execute(
        """
        UPDATE recruit_reviews
        SET status = UPPER(TRIM(COALESCE(status, 'NEW')))
        """
    )

    allowed = ", ".join(f"'{value}'" for value in VALID_STATUSES)
    op.execute(
        f"""
        UPDATE recruit_reviews
        SET status = 'NEW'
        WHERE status NOT IN ({allowed})
        """
    )

    with op.batch_alter_table("recruit_reviews", schema=None) as batch_op:
        batch_op.add_column(sa.Column("labeled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("label_reason", sa.String(), nullable=True))
        batch_op.alter_column(
            "status",
            existing_type=sa.String(),
            nullable=False,
            server_default="NEW",
        )
        batch_op.create_check_constraint(
            "ck_recruit_reviews_status_phase2",
            f"status IN ({allowed})",
        )
        batch_op.create_index(
            "ix_recruit_reviews_status_labeled_at",
            ["status", "labeled_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("recruit_reviews", schema=None) as batch_op:
        batch_op.drop_index("ix_recruit_reviews_status_labeled_at")
        batch_op.drop_constraint("ck_recruit_reviews_status_phase2", type_="check")
        batch_op.alter_column(
            "status",
            existing_type=sa.String(),
            nullable=True,
            server_default=None,
        )
        batch_op.drop_column("label_reason")
        batch_op.drop_column("labeled_at")
