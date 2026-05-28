# backend/app/models/track.py
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, func, ARRAY, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..db.base import Base

if TYPE_CHECKING:
    from .artist import Artist
    from .user import User
    from .playlist_track import PlaylistTrack
    from .user_like import UserLike

class Track(Base):
    __tablename__ = "tracks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jamendo_id: Mapped[Optional[int]] = mapped_column(unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artists.id"), nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Время последнего обновления play_url (уже было)
    play_url_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Статус доступности трека: False — запись сохранена, но воспроизведение недоступно (битый URL на Jamendo)
    is_available: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    is_user_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploader_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    moderation_status: Mapped[str] = mapped_column(
        String(20), default="approved", server_default="approved", nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    artist: Mapped["Artist | None"] = relationship("Artist", back_populates="tracks")
    playlist_items: Mapped[List["PlaylistTrack"]] = relationship("PlaylistTrack", back_populates="track", cascade="all, delete-orphan")
    uploader: Mapped["User | None"] = relationship("User", foreign_keys=[uploader_id], back_populates="uploaded_tracks")
    likers: Mapped[List["UserLike"]] = relationship("UserLike", back_populates="track", viewonly=True)
    liked_by: Mapped[List["UserLike"]] = relationship("UserLike", back_populates="track", viewonly=True)