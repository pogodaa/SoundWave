# backend/tests/conftest.py
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.models.user import User
from app.models.artist import Artist
from app.core.security import get_password_hash
from app.db.session import get_db

from httpx import AsyncClient
from app.main import app


# Явное определение строки подключения для тестов
# Приоритет: 1) TEST_DATABASE_URL из env, 2) локальный localhost, 3) Docker-хост
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://soundwave:soundwave@localhost:5432/soundwave_test"
)


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Асинхронный движок для тестов"""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def setup_test_db(engine):
    """Создание/очистка схемы БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(engine, setup_test_db):
    """Сессия БД с откатом после теста"""
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session):
    """HTTP-клиент с подменой get_db"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Тестовый пользователь"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("SecurePass123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_artist(db_session: AsyncSession):
    """Тестовый исполнитель"""
    artist = Artist(
        jamendo_id=1,
        name="Test Artist",
        image_url="https://example.com/artist.jpg"
    )
    db_session.add(artist)
    await db_session.commit()
    await db_session.refresh(artist)
    return artist