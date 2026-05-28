# backend/app/models/artist.py
from __future__ import annotations
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..db.base import Base

if TYPE_CHECKING:
    from .track import Track

class Artist(Base):
    __tablename__ = "artists"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jamendo_id: Mapped[int | None] = mapped_column(unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Для пользовательских артистов
    is_user_uploaded: Mapped[bool] = mapped_column(default=False, nullable=False)
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 🔹 Обратная связь с Track (явная, через back_populates)
    tracks: Mapped[List["Track"]] = relationship("Track", back_populates="artist")