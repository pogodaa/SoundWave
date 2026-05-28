# backend/app/schemas/track.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class TrackRead(BaseModel):
    """Схема ответа API. Дефолты применяются ТОЛЬКО при возврате клиенту."""
    id: Optional[int] = None
    jamendo_id: Optional[int] = None

    # Доступность воспроизведения (битые ссылки Jamendo помечаются на бэкенде)
    is_available: bool = True
    
    # Критические поля (обязательные)
    title: str = Field(..., min_length=1)
    audio_url: str = Field(...)
    
    # Опциональные поля (дефолты при None)
    artist_name: Optional[str] = Field(default="Неизвестный исполнитель")
    album_name: Optional[str] = Field(default=None)
    duration: Optional[int] = Field(default=0, ge=0)
    genre: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    cover_url: Optional[str] = Field(default="/covers/default.png")
    releasedate: Optional[str] = Field(default=None)
    is_user_uploaded: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)