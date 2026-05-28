# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Новый импорт (instance settings)
from ..core.config import settings

# ====================== ASYNC ENGINE ======================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,           # можно поставить True для отладки
    future=True,
)

# ====================== SESSIONMAKER ======================
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ====================== DEPENDENCY ======================
async def get_db():
    """Dependency для FastAPI (используется в роутерах)"""
    async with AsyncSessionLocal() as session:
        yield session