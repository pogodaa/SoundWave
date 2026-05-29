"""extend user avatar_url length

Revision ID: f7a8b9c0d1e2
Revises: e4c2f1ab0d99
Create Date: 2026-05-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, None] = 'e4c2f1ab0d99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Увеличиваем длину avatar_url для путей вида /static/avatars/<uuid>.ext
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'avatar_url',
            existing_type=sa.String(length=255),
            type_=sa.String(length=512),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'avatar_url',
            existing_type=sa.String(length=512),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
