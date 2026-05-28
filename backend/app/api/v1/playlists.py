# backend/app/api/v1/playlists.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.models.track import Track
from app.models.artist import Artist
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate, AddTrackRequest, PlaylistRead, PlaylistTrackRead
from app.services.playlist_service import (
    create_playlist, get_user_playlists, get_playlist_by_id,
    get_playlist_tracks, update_playlist, delete_playlist, 
    add_track_to_playlist, remove_track_from_playlist, reorder_tracks
)

router = APIRouter(prefix="/playlists", tags=["playlists"])

async def _build_playlist_read(db: AsyncSession, playlist: Playlist) -> PlaylistRead:
    """Вспомогательная функция для построения полного ответа с треками"""
    tracks_data = await get_playlist_tracks(db, playlist.id)
    tracks = [PlaylistTrackRead(**track) for track in tracks_data]
    
    return PlaylistRead(
        id=playlist.id,
        user_id=playlist.user_id,
        name=playlist.name,
        description=playlist.description,
        is_public=playlist.is_public,
        share_token=playlist.share_token,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        tracks=tracks
    )

@router.post("", response_model=PlaylistRead, status_code=status.HTTP_201_CREATED)
async def create_new_playlist(
    data: PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    playlist = await create_playlist(db, current_user.id, data)
    return await _build_playlist_read(db, playlist)

@router.get("", response_model=List[PlaylistRead])
async def get_my_playlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    playlists = await get_user_playlists(db, current_user.id)
    result = []
    for playlist in playlists:
        result.append(await _build_playlist_read(db, playlist))
    return result

@router.get("/{playlist_id}", response_model=PlaylistRead)
async def get_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    playlist = await get_playlist_by_id(db, playlist_id, current_user.id)
    return await _build_playlist_read(db, playlist)

@router.patch("/{playlist_id}", response_model=PlaylistRead)
async def update_playlist_endpoint(
    playlist_id: int,
    data: PlaylistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    playlist = await update_playlist(db, playlist_id, current_user.id, data)
    return await _build_playlist_read(db, playlist)

@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist_endpoint(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await delete_playlist(db, playlist_id, current_user.id)
    return None

@router.post("/{playlist_id}/tracks", response_model=PlaylistRead)
async def add_track_endpoint(
    playlist_id: int,
    data: AddTrackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    playlist = await add_track_to_playlist(db, playlist_id, current_user.id, data)
    return await _build_playlist_read(db, playlist)

@router.delete("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_track_endpoint(
    playlist_id: int,
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await remove_track_from_playlist(db, playlist_id, current_user.id, track_id)
    return None

@router.put("/{playlist_id}/tracks/reorder", response_model=PlaylistRead)
async def reorder_tracks_endpoint(
    playlist_id: int,
    track_positions: dict[str, int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Преобразуем ключи из str в int
    positions = {int(k): v for k, v in track_positions.items()}
    await reorder_tracks(db, playlist_id, current_user.id, positions)
    playlist = await get_playlist_by_id(db, playlist_id, current_user.id)
    return await _build_playlist_read(db, playlist)