"""merge migration heads

Revision ID: 6f30876a5f86
Revises: 669a57831bf7, 79eb5d6963d3
Create Date: 2026-03-26 10:46:57.499901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f30876a5f86'
down_revision: Union[str, Sequence[str], None] = ('669a57831bf7', '79eb5d6963d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
