# backend/app/services/playlist_service.py
import logging
import secrets
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.models.track import Track
from app.models.artist import Artist
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate, AddTrackRequest

logger = logging.getLogger(__name__)

async def create_playlist(db: AsyncSession, user_id: int, data: PlaylistCreate) -> Playlist:
    share_token = secrets.token_urlsafe(16) if data.is_public else None
    new_playlist = Playlist(
        user_id=user_id,
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        share_token=share_token
    )
    db.add(new_playlist)
    await db.commit()
    await db.refresh(new_playlist)
    logger.info(f"Плейлист создан: id={new_playlist.id}, user={user_id}")
    return new_playlist

async def get_user_playlists(db: AsyncSession, user_id: int) -> list[Playlist]:
    stmt = select(Playlist).where(Playlist.user_id == user_id).order_by(Playlist.updated_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_playlist_by_id(db: AsyncSession, playlist_id: int, user_id: int) -> Playlist:
    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Плейлист не найден")
    if playlist.user_id != user_id and not playlist.is_public:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return playlist

async def get_playlist_tracks(db: AsyncSession, playlist_id: int) -> list[dict]:
    stmt = (
        select(PlaylistTrack, Track, Artist.name.label("artist_name"))
        .join(Track, PlaylistTrack.track_id == Track.id)
        .outerjoin(Artist, Track.artist_id == Artist.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
    )
    result = await db.execute(stmt)
    tracks = []
    for pt, track, artist_name in result.all():
        tags = track.tags or []
        if not isinstance(tags, list):
            tags = []
        tracks.append({
            "track_id": track.id,
            "jamendo_id": track.jamendo_id,
            "title": track.title,
            "artist_name": artist_name or "Неизвестный исполнитель",
            "duration": track.duration,
            "audio_url": track.audio_url,
            "cover_url": track.image_url or "/covers/default.png",
            "genre": track.genre,
            "tags": tags,
            "is_user_uploaded": track.is_user_uploaded,
            "is_available": track.is_available,
            "position": pt.position,
        })
    return tracks

async def update_playlist(db: AsyncSession, playlist_id: int, user_id: int, data: PlaylistUpdate) -> Playlist:
    playlist = await get_playlist_by_id(db, playlist_id, user_id)
    
    if data.name is not None:
        playlist.name = data.name
    if data.description is not None:
        playlist.description = data.description
    if data.is_public is not None:
        playlist.is_public = data.is_public
        playlist.share_token = secrets.token_urlsafe(16) if data.is_public else None

    await db.commit()
    await db.refresh(playlist)
    return playlist

async def delete_playlist(db: AsyncSession, playlist_id: int, user_id: int) -> bool:
    playlist = await get_playlist_by_id(db, playlist_id, user_id)
    await db.delete(playlist)
    await db.commit()
    return True

async def add_track_to_playlist(db: AsyncSession, playlist_id: int, user_id: int, data: AddTrackRequest) -> Playlist:
    playlist = await get_playlist_by_id(db, playlist_id, user_id)
    
    # Проверяем существование трека
    track_stmt = select(Track).where(Track.id == data.track_id)
    track_result = await db.execute(track_stmt)
    if not track_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Трек не найден в базе")

    # Проверяем дубликаты
    exists_stmt = select(PlaylistTrack).where(
        PlaylistTrack.playlist_id == playlist_id,
        PlaylistTrack.track_id == data.track_id
    )
    if (await db.execute(exists_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Трек уже в плейлисте")

    # Определяем позицию
    if data.position is not None:
        # Сдвигаем существующие треки
        stmt = select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.position >= data.position
        )
        result = await db.execute(stmt)
        for pt in result.scalars().all():
            pt.position += 1
        new_pos = data.position
    else:
        pos_stmt = select(PlaylistTrack.position).where(PlaylistTrack.playlist_id == playlist_id)
        pos_result = await db.execute(pos_stmt)
        positions = [r[0] for r in pos_result.all()]
        new_pos = max(positions) + 1 if positions else 1

    db.add(PlaylistTrack(playlist_id=playlist_id, track_id=data.track_id, position=new_pos))
    await db.commit()
    await db.refresh(playlist)
    return playlist

async def remove_track_from_playlist(db: AsyncSession, playlist_id: int, user_id: int, track_id: int) -> bool:
    playlist = await get_playlist_by_id(db, playlist_id, user_id)
    
    stmt = delete(PlaylistTrack).where(
        PlaylistTrack.playlist_id == playlist_id,
        PlaylistTrack.track_id == track_id
    )
    await db.execute(stmt)
    await db.commit()
    return True

async def reorder_tracks(db: AsyncSession, playlist_id: int, user_id: int, track_positions: dict[int, int]) -> bool:
    """
    Изменение порядка треков в плейлисте.
    track_positions: {track_id: new_position}
    """
    playlist = await get_playlist_by_id(db, playlist_id, user_id)
    
    for track_id, position in track_positions.items():
        stmt = (
            update(PlaylistTrack)
            .where(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id
            )
            .values(position=position)
        )
        await db.execute(stmt)
    
    await db.commit()
    return True