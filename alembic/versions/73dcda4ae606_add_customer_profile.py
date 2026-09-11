"""Add customer profile

Revision ID: 73dcda4ae606
Revises: 754af73bfd6f
Create Date: 2026-09-09 23:19:53.657125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73dcda4ae606'
down_revision: Union[str, Sequence[str], None] = '754af73bfd6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Legacy revision retained after the baseline schema repair.

    ``customers`` is now part of the repaired baseline migration.
    """


def downgrade() -> None:
    """No-op; the baseline downgrade removes the customers table."""
