# backend/migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

# 🔹 Загружаем переменные окружения
load_dotenv()

# 🔹 1. Сначала импортируем Base
from app.db.base import Base

# 🔹 2. Затем импортируем ВСЕ модели — это регистрирует их в Base.metadata
# ВАЖНО: импортировать модули, а не классы, чтобы избежать циклических импортов
from app.models import (  # noqa: F401
    user,
    artist,
    track,
    playlist,
    playlist_track,
    user_like,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔹 3. Только ПОСЛЕ импорта моделей устанавливаем target_metadata
target_metadata = Base.metadata

# 🔹 4. Переопределяем URL из .env (заменяем asyncpg на psycopg2 для миграций)
database_url = os.getenv("DATABASE_URL")
if database_url and "asyncpg" in database_url:
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    config.set_main_option("sqlalchemy.url", database_url)

# 🔹 Отладка: выведи список таблиц в консоль при генерации миграции
import sys
print(f"🔍 Tables in metadata: {list(target_metadata.tables.keys())}", file=sys.stderr)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()