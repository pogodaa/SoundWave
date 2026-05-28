"""drop user_history table

Revision ID: e4c2f1ab0d99
Revises: 9b0eb85f6a46
Create Date: 2026-05-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4c2f1ab0d99'
down_revision: Union[str, None] = '9b0eb85f6a46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Удаляем таблицу истории прослушиваний (рекомендации строятся только на лайках)."""
    op.execute(sa.text("DROP TABLE IF EXISTS user_history CASCADE"))


def downgrade() -> None:
    """Восстановление таблицы не выполняется — данные истории не используются в продукте."""
    pass
