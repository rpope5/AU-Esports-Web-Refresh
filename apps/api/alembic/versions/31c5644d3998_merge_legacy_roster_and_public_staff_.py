"""Merge legacy roster and public staff profile heads

Revision ID: 31c5644d3998
Revises: b7a4f0d2c91e, f2c1a7d58b31
Create Date: 2026-05-06 12:53:31.380639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31c5644d3998'
down_revision: Union[str, Sequence[str], None] = ('b7a4f0d2c91e', 'f2c1a7d58b31')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
