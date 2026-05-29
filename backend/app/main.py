# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import logging

# Настройки приложения
from .core.config import settings
from .db.session import engine
from .db.base import Base
from .api.v1 import auth, users, tracks, playlists, interactions, recommendations

# Настройка логгера
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Логирование при старте приложения
    logger.info("Запуск приложения")
    logger.info(f"LASTFM_API_KEY: {'загружен' if settings.LASTFM_API_KEY else 'отсутствует'}")
    logger.info(f"JAMENDO_CLIENT_ID: {'загружен' if settings.JAMENDO_CLIENT_ID else 'отсутствует'}")
    
    # Примечание: Alembic управляет миграциями, create_all не требуется
    # Если нужно создать таблицы вручную (только для отладки):
    # if settings.DEBUG:
    #     async with engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.create_all)
    #     logger.info("Таблицы базы данных созданы")
    
    yield
    
    # Очистка ресурсов при завершении
    logger.info("Завершение работы приложения")
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Музыкальный стриминговый сервис с системой рекомендаций на основе машинного обучения",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация роутеров API
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(tracks.router, prefix="/api/v1")
app.include_router(playlists.router, prefix="/api/v1")
app.include_router(interactions.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")

# Раздача загруженных аватаров
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Эндпоинт проверки здоровья сервиса
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SoundWave Backend"}

# Эндпоинт для отладки конфигурации (безопасный вывод)
@app.get("/debug-config")
async def debug_config():
    return {
        "LASTFM_API_KEY_loaded": settings.LASTFM_API_KEY is not None,
        "LASTFM_API_KEY_preview": (
            settings.LASTFM_API_KEY[:4] + "..." 
            if settings.LASTFM_API_KEY else None
        ),
        "JAMENDO_CLIENT_ID_loaded": settings.JAMENDO_CLIENT_ID is not None,
        "BREVO_API_KEY_loaded": settings.BREVO_API_KEY is not None,
        "DEBUG_MODE": settings.DEBUG,
    }

# Точка входа для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )