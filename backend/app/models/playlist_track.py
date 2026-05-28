# backend/app/models/playlist_track.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..db.base import Base

if TYPE_CHECKING:
    from .playlist import Playlist
    from .track import Track

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id"), primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="playlist_tracks")
    track: Mapped["Track"] = relationship("Track", back_populates="playlist_items")