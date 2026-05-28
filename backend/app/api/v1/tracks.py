# backend/app/api/v1/tracks.py
from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Query, Depends, BackgroundTasks, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.track import TrackRead
from app.services.track_service import (
    search_tracks_with_cache,
    get_popular_with_cache,
    get_fresh_play_url,
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracks", tags=["tracks"])

@router.get("/search", response_model=List[TrackRead])
async def search_tracks(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Поиск треков с кэшированием: БД -> Jamendo -> Сохранение -> Возврат"""
    return await search_tracks_with_cache(
        db,
        query=q,
        limit=limit,
        background_tasks=background_tasks
    )

@router.get("/popular", response_model=List[TrackRead])
async def get_popular_tracks(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """Популярные треки с кэшированием и обработкой битых ссылок."""
    return await get_popular_with_cache(
        db,
        limit=limit,
        background_tasks=background_tasks,
    )

@router.get("/{track_id}/play-url")
async def get_play_url(
    track_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает актуальную прямую ссылку для воспроизведения.
    Если токен в БД истёк (>2 часов), запрашивает свежие метаданные у Jamendo API,
    обновляет ссылку в БД и возвращает её.
    
    Фронтенд использует эту ссылку напрямую в <audio src="...">.
    """
    try:
        fresh_url = await get_fresh_play_url(db, track_id)
        return {
            "audio_url": fresh_url,
            "track_id": track_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
            "refreshed": True
        }
    except HTTPException as e:
        # Пробрасываем ошибки 404/502 от Jamendo
        raise e
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении ссылки для трека {track_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при подготовке ссылки для воспроизведения"
        )