# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ==================== Основные настройки ====================
    DATABASE_URL: str = Field(..., description="URL подключения к БД")
    SECRET_KEY: str = Field(..., min_length=32, description="Секретный ключ для JWT")
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY должен быть не менее 32 символов')
        return v
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # ← Изменил на 30 для консистентности

    # ==================== API Ключи ====================
    JAMENDO_CLIENT_ID: Optional[str] = None
    LASTFM_API_KEY: Optional[str] = None

    # ==================== Почта (Brevo) ====================
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: str = "no-reply@soundwave.local"
    BREVO_SENDER_NAME: str = "SoundWave"

    # ==================== Дополнительно ====================
    PROJECT_NAME: str = "SoundWave"
    DEBUG: bool = True
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

settings = Settings()