# backend/app/services/interaction_service.py — Бизнес-логика лайков (рекомендации только по лайкам)
import logging
from sqlalchemy import select, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.artist import Artist
from app.models.track import Track
from app.models.user_like import UserLike
from app.schemas.interactions import LikedTrackItem, UserInteractionsSummary
from app.schemas.track import TrackRead

logger = logging.getLogger(__name__)


def _track_to_trackread(track: Track, artist_name: str | None) -> TrackRead:
    """ORM Track → TrackRead для ответа API."""
    tags = track.tags or []
    if not isinstance(tags, list):
        tags = []
    return TrackRead(
        id=track.id,
        jamendo_id=track.jamendo_id,
        is_available=track.is_available,
        title=track.title,
        audio_url=track.audio_url,
        artist_name=artist_name or "Неизвестный исполнитель",
        album_name=None,
        duration=int(track.duration or 0),
        genre=track.genre,
        tags=tags,
        cover_url=track.image_url or "/covers/default.png",
        releasedate=None,
        is_user_uploaded=track.is_user_uploaded,
        created_at=track.added_at,
        updated_at=track.updated_at,
    )


async def toggle_like(db: AsyncSession, user_id: int, track_id: int) -> dict:
    """Добавление лайка. Если лайк уже стоит — ошибка 400."""
    track_check = await db.execute(select(Track).where(Track.id == track_id))
    if not track_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Трек не найден")

    like_check = await db.execute(
        select(UserLike).where(
            UserLike.user_id == user_id,
            UserLike.track_id == track_id,
        )
    )
    if like_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Лайк уже установлен")

    new_like = UserLike(user_id=user_id, track_id=track_id)
    db.add(new_like)
    await db.commit()
    logger.info(f"Пользователь {user_id} лайкнул трек {track_id}")
    return {"message": "Лайк добавлен"}


async def remove_like(db: AsyncSession, user_id: int, track_id: int) -> dict:
    """Удаление лайка."""
    stmt = delete(UserLike).where(
        UserLike.user_id == user_id,
        UserLike.track_id == track_id,
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лайк не найден")

    logger.info(f"Пользователь {user_id} убрал лайк с трека {track_id}")
    return {"message": "Лайк удален"}


async def get_user_likes(db: AsyncSession, user_id: int, limit: int = 50) -> list[LikedTrackItem]:
    """Список лайков с полными данными трека (включая is_available = False)."""
    stmt = (
        select(UserLike, Track, Artist.name.label("artist_name_for_response"))
        .join(Track, UserLike.track_id == Track.id)
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(UserLike.user_id == user_id)
        .order_by(desc(UserLike.liked_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items: list[LikedTrackItem] = []
    for like, track, artist_name in rows:
        items.append(
            LikedTrackItem(
                liked_at=like.liked_at,
                track=_track_to_trackread(track, artist_name),
            )
        )
    return items


async def is_track_liked(db: AsyncSession, user_id: int, track_id: int) -> bool:
    """Проверка, лайкнут ли конкретный трек пользователем."""
    stmt = select(UserLike).where(
        UserLike.user_id == user_id,
        UserLike.track_id == track_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_user_interactions_summary(db: AsyncSession, user_id: int) -> UserInteractionsSummary:
    """
    Сводка по взаимодействиям пользователя для рекомендательной системы.
    Учитываются только лайки (история прослушиваний не хранится).
    """
    likes_count = await db.execute(
        select(func.count(UserLike.user_id)).where(UserLike.user_id == user_id)
    )
    total_likes = likes_count.scalar_one() or 0

    genre_query = (
        select(Track.genre, func.count(Track.genre).label("cnt"))
        .join(UserLike, Track.id == UserLike.track_id)
        .where(UserLike.user_id == user_id, Track.genre.isnot(None))
        .group_by(Track.genre)
        .order_by(desc("cnt"))
        .limit(3)
    )
    genre_result = await db.execute(genre_query)
    favorite_genres = [row[0] for row in genre_result.all() if row[0]]

    return UserInteractionsSummary(
        total_likes=total_likes,
        total_listens=0,
        favorite_genres=favorite_genres,
    )
