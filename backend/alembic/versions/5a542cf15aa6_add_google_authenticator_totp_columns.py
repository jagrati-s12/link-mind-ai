"""add_google_authenticator_totp_columns

Revision ID: 5a542cf15aa6
Revises: 1d9ed236cd4a
Create Date: 2026-10-23 23:42:57.233913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a542cf15aa6'
down_revision: Union[str, Sequence[str], None] = '1d9ed236cd4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('totp_secret', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('is_totp_enabled', sa.Boolean(), nullable=True, server_default=sa.text('0')))
    op.add_column('users', sa.Column('totp_temp_secret', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'totp_temp_secret')
    op.drop_column('users', 'is_totp_enabled')
    op.drop_column('users', 'totp_secret')
