"""change of auth/hashed_password

Revision ID: d9e84722b27b
Revises: 484391c075b7
Create Date: 2025-06-23 16:12:59.721228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e84722b27b'
down_revision: Union[str, None] = '484391c075b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('users', 'hashed_password')
    op.add_column('users', sa.Column('hashed_password', sa.LargeBinary(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')
    op.add_column('users', sa.Column('hashed_password', sa.String(length=128), nullable=False))
