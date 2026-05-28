# backend/app/models/user.py
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..db.base import Base
from .user_like import UserLike

if TYPE_CHECKING:
    from .playlist import Playlist
    from .track import Track

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(255), 
        default="/avatars/default1.png",
        server_default="/avatars/default1.png",
        nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(20), 
        default="unverified",
        server_default="unverified",
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    playlists: Mapped[List["Playlist"]] = relationship("Playlist", back_populates="user", cascade="all, delete-orphan")
    
    likes: Mapped[List["UserLike"]] = relationship(
        "UserLike", back_populates="user", cascade="all, delete-orphan"
    )
    
    uploaded_tracks: Mapped[List["Track"]] = relationship(
        "Track",
        foreign_keys="[Track.uploader_id]",
        back_populates="uploader",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"