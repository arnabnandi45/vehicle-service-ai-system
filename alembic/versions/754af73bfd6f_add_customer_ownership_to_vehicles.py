"""Add customer ownership to vehicles

Revision ID: 754af73bfd6f
Revises: 1d75bbd4063f
Create Date: 2026-09-09 15:02:36.623935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '754af73bfd6f'
down_revision: Union[str, Sequence[str], None] = '1d75bbd4063f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Legacy revision retained after the baseline schema repair.

    ``vehicles.customer_id`` and its foreign key are now part of the repaired
    baseline migration.
    """


def downgrade() -> None:
    """No-op; the baseline downgrade removes the vehicles table."""
