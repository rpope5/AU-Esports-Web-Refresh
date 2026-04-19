"""Add admin user management fields.

Revision ID: 7f3b6c1a9e42
Revises: d3adb3158f10
Create Date: 2026-04-18 14:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f3b6c1a9e42"
down_revision: Union[str, Sequence[str], None] = "d3adb3158f10"
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


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "admin_users"):
        return

    with op.batch_alter_table("admin_users", schema=None) as batch_op:
        if not _column_exists(bind, "admin_users", "is_active"):
            batch_op.add_column(
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
            )
        if not _column_exists(bind, "admin_users", "must_change_password"):
            batch_op.add_column(
                sa.Column(
                    "must_change_password",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
        if not _column_exists(bind, "admin_users", "created_at"):
            batch_op.add_column(
                sa.Column("created_at", sa.DateTime(), nullable=True)
            )
        if not _column_exists(bind, "admin_users", "updated_at"):
            batch_op.add_column(
                sa.Column("updated_at", sa.DateTime(), nullable=True)
            )

    op.execute(
        sa.text(
            "UPDATE admin_users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE admin_users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "admin_users"):
        return

    with op.batch_alter_table("admin_users", schema=None) as batch_op:
        if _column_exists(bind, "admin_users", "updated_at"):
            batch_op.drop_column("updated_at")
        if _column_exists(bind, "admin_users", "created_at"):
            batch_op.drop_column("created_at")
        if _column_exists(bind, "admin_users", "must_change_password"):
            batch_op.drop_column("must_change_password")
        if _column_exists(bind, "admin_users", "is_active"):
            batch_op.drop_column("is_active")
