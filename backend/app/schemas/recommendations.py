# backend/app/schemas/recommendations.py
from pydantic import BaseModel, Field
from typing import List

from app.schemas.track import TrackRead


class PersonalRecommendationsResponse(BaseModel):
    """Ответ персональных рекомендаций с флагом холодного старта."""

    tracks: List[TrackRead] = Field(default_factory=list)
    cold_start: bool = Field(
        default=False,
        description="True, если у пользователя нет лайков и ML-профиль не построен",
    )
    used_popular_fallback: bool = Field(
        default=False,
        description="True, если вместо ML вернули популярные (нет жанров/тегов у лайков)",
    )
