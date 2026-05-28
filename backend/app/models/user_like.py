# backend/app/models/user_like.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..db.base import Base

if TYPE_CHECKING:
    from .user import User
    from .track import Track

class UserLike(Base):
    __tablename__ = "user_likes"
    
    # Составной первичный ключ: один юзер может лайкнуть трек только один раз
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    
    liked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship("User", back_populates="likes")
    track: Mapped["Track"] = relationship("Track", back_populates="liked_by")