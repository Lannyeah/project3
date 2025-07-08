"""change of auth/hashed_password

Revision ID: d9e84722b27b
Revises: 484391c075b7
Create Date: 2025-06-23 16:12:59.721228

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd9e84722b27b'
down_revision: str | None = '484391c075b7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('users', 'hashed_password')
    op.add_column('users', sa.Column('hashed_password', sa.LargeBinary(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')
    op.add_column('users', sa.Column('hashed_password', sa.String(length=128), nullable=False))
