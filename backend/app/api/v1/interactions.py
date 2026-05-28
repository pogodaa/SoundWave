# backend/app/api/v1/interactions.py — Эндпоинты для лайков и сводки для рекомендаций
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.interactions import LikeResponse, LikedTrackItem, UserInteractionsSummary
from app.services.interaction_service import (
    toggle_like,
    remove_like,
    get_user_likes,
    get_user_interactions_summary,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/like/{track_id}", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
async def like_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Добавить лайк к треку"""
    return await toggle_like(db, current_user.id, track_id)


@router.delete("/like/{track_id}", response_model=LikeResponse)
async def unlike_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить лайк с трека"""
    return await remove_like(db, current_user.id, track_id)


@router.get("/likes", response_model=list[LikedTrackItem])
async def get_my_likes(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить лайки с метаданными треков (в т.ч. недоступные на Jamendo)."""
    return await get_user_likes(db, current_user.id, limit)


@router.get("/summary", response_model=UserInteractionsSummary)
async def get_interactions_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сводка по взаимодействиям (для ML-рекомендаций на основе лайков)"""
    return await get_user_interactions_summary(db, current_user.id)
