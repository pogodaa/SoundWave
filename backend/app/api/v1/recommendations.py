# backend/app/api/v1/recommendations.py
import logging

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recommendations import PersonalRecommendationsResponse
from app.services.recommendation_service import get_personal_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/personal", response_model=PersonalRecommendationsResponse)
async def personal_recommendations(
    limit: int = Query(20, ge=1, le=50, description="Количество рекомендуемых треков"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Персональные рекомендации на основе лайков (Content-Based, scikit-learn).

    user_id берётся из JWT-токена авторизации.
    """
    return await get_personal_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        background_tasks=background_tasks,
    )
