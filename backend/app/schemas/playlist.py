# backend/app/schemas/playlist.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class PlaylistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    # Личные плейлисты по умолчанию (только владелец через API)
    is_public: bool = False

class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_public: Optional[bool] = None

class AddTrackRequest(BaseModel):
    track_id: int = Field(..., description="ID трека из БД/Jamendo")
    position: Optional[int] = Field(default=None, ge=1)

class ReorderTracksRequest(BaseModel):
    track_positions: dict[str, int] = Field(..., description="Словарь {track_id: new_position}")

class PlaylistTrackRead(BaseModel):
    track_id: int
    jamendo_id: Optional[int] = None
    title: str
    artist_name: Optional[str] = "Неизвестный исполнитель"
    duration: Optional[int] = 0
    audio_url: str
    cover_url: Optional[str] = "/covers/default.png"
    genre: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_user_uploaded: bool = False
    is_available: bool = True
    position: int
    model_config = ConfigDict(from_attributes=True)

class PlaylistRead(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    is_public: bool
    share_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    tracks: List[PlaylistTrackRead] = []
    model_config = ConfigDict(from_attributes=True)