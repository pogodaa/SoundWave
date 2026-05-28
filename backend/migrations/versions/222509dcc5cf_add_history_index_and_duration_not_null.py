"""историческая ревизия: ранее менялась таблица user_history (удалена из проекта)

Revision ID: 222509dcc5cf
Revises: 0f0a3a02c6f6
Create Date: 2026-05-09 01:27:23.143483

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '222509dcc5cf'
down_revision: Union[str, None] = '0f0a3a02c6f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Таблица user_history исключена из модели — миграция оставлена для целостности цепочки Alembic."""
    pass


def downgrade() -> None:
    pass
