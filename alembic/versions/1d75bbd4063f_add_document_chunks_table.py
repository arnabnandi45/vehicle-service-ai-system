"""add document chunks table

Revision ID: 1d75bbd4063f
Revises: 1ed10155e269
Create Date: 2026-09-03 15:13:49.588133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d75bbd4063f'
down_revision: Union[str, Sequence[str], None] = '1ed10155e269'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Legacy revision retained after the baseline schema repair.

    ``document_chunks`` is now created by the repaired baseline migration so
    that a fresh database can be built from the complete revision chain.
    """


def downgrade() -> None:
    """No-op; the baseline downgrade removes ``document_chunks``."""
