"""Add public staff profiles table.

Revision ID: f2c1a7d58b31
Revises: 12403619f017
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2c1a7d58b31"
down_revision: Union[str, Sequence[str], None] = "12403619f017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "staff_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("preferred_name", sa.String(length=160), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("game_scope", sa.JSON(), nullable=True),
        sa.Column("year_label", sa.String(length=120), nullable=True),
        sa.Column("previous_college", sa.String(length=160), nullable=True),
        sa.Column("bio_at_ashland", sa.JSON(), nullable=True),
        sa.Column("bio_before_ashland", sa.JSON(), nullable=True),
        sa.Column("responsibilities", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("staff_profiles", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_staff_profiles_category"), ["category"], unique=False)
        batch_op.create_index(batch_op.f("ix_staff_profiles_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_staff_profiles_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_staff_profiles_slug"), ["slug"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("staff_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_staff_profiles_slug"))
        batch_op.drop_index(batch_op.f("ix_staff_profiles_is_active"))
        batch_op.drop_index(batch_op.f("ix_staff_profiles_id"))
        batch_op.drop_index(batch_op.f("ix_staff_profiles_category"))

    op.drop_table("staff_profiles")
