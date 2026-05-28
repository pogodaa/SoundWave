# backend/app/schemas/interactions.py — Pydantic-схемы для лайков и сводки рекомендаций
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from app.schemas.track import TrackRead


class LikeResponse(BaseModel):
    """Ответ на операции с лайками"""
    message: str
    model_config = ConfigDict(from_attributes=True)


class LikedTrackItem(BaseModel):
    """Лайк с полными данными трека (для страницы «Понравившиеся», в т.ч. недоступные)."""
    liked_at: datetime
    track: TrackRead
    model_config = ConfigDict(from_attributes=True)


class UserInteractionsSummary(BaseModel):
    """
    Сводка по взаимодействиям пользователя (для рекомендаций).
    Поле total_listens оставлено для обратной совместимости API и всегда 0.
    """
    total_likes: int
    total_listens: int = Field(default=0, description="Не используется; история прослушиваний отключена")
    favorite_genres: list[str]
    model_config = ConfigDict(from_attributes=True)
