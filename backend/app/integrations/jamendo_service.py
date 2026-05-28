# backend/app/integrations/jamendo_service.py
import httpx
import logging
from app.core.config import settings
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

JAMENDO_BASE = "https://api.jamendo.com/v3.0"
REQUIRED_FIELDS = ["id", "name", "audio"]


def is_track_valid(track: Dict[str, Any]) -> bool:
    """Проверяет, что трек содержит обязательные поля"""
    return all(track.get(field) for field in REQUIRED_FIELDS)


def parse_jamendo_track_raw(track: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Парсит ответ Jamendo. Возвращает None, если трек невалиден."""
    if not is_track_valid(track):
        return None
    
    tags = track.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif not isinstance(tags, list):
        tags = []

    return {
        "id": int(track.get("id")),
        "jamendo_id": int(track.get("id")),
        "title": track.get("name"),
        "artist_name": track.get("artist_name"),
        "album_name": track.get("album_name"),
        "duration": track.get("duration"),
        "genre": tags[0] if tags else None,
        "tags": tags,
        "audio_url": track.get("audio"),
        "image_url": track.get("image"),
        "cover_url": track.get("image"),
        "releasedate": track.get("releasedate"),
        "is_user_uploaded": False,
    }


async def get_random_tracks(limit: int = 50) -> List[Dict[str, Any]]:
    """Получает случайные треки (используется для пула популярных)"""
    fetch_limit = int(limit * 1.5)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{JAMENDO_BASE}/tracks/",
            params={
                "client_id": settings.JAMENDO_CLIENT_ID,
                "format": "json",
                "limit": fetch_limit,
                "order": "random",
                "include": "musicinfo",
                "audioformat": "mp32"
            },
            timeout=20.0
        )
        
        if response.status_code != 200:
            logger.error(f"Jamendo random error: {response.status_code}")
            return []
        
        raw = response.json().get("results", [])
        valid = []
        for t in raw:
            parsed = parse_jamendo_track_raw(t)
            if parsed:
                valid.append(parsed)
            if len(valid) >= limit:
                break
        return valid


# Остальные функции (search_tracks, get_popular_tracks, fetch_track_by_id, get_fresh_track_url) оставляем без изменений


async def search_tracks(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Поиск треков с фильтрацией невалидных"""
    fetch_limit = int(limit * 1.5)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{JAMENDO_BASE}/tracks/",
            params={
                "client_id": settings.JAMENDO_CLIENT_ID,
                "format": "json",
                "limit": fetch_limit,
                "namesearch": query,
                "order": "popularity_total",
                "include": "musicinfo",
                "audioformat": "mp32"
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            logger.error(f"Jamendo search error: {response.status_code}")
            return []
        
        raw = response.json().get("results", [])
        valid = []
        for t in raw:
            parsed = parse_jamendo_track_raw(t)
            if parsed:
                valid.append(parsed)
            if len(valid) >= limit:
                break
        return valid


async def get_popular_tracks(limit: int = 20) -> List[Dict[str, Any]]:
    """Популярные треки — аналогично с фильтрацией"""
    fetch_limit = int(limit * 1.5)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{JAMENDO_BASE}/tracks/",
            params={
                "client_id": settings.JAMENDO_CLIENT_ID,
                "format": "json",
                "limit": fetch_limit,
                "order": "popularity_total",
                "include": "musicinfo",
                "audioformat": "mp32"
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            logger.error(f"Jamendo popular error: {response.status_code}")
            return []
        
        raw = response.json().get("results", [])
        valid = []
        for t in raw:
            parsed = parse_jamendo_track_raw(t)
            if parsed:
                valid.append(parsed)
            if len(valid) >= limit:
                break
        return valid


async def fetch_track_by_id(jamendo_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные одного трека по Jamendo ID"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{JAMENDO_BASE}/tracks/",
            params={
                "client_id": settings.JAMENDO_CLIENT_ID,
                "id": jamendo_id,
                "format": "json",
                "include": "musicinfo",
                "audioformat": "mp32"
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            return None
        
        results = response.json().get("results", [])
        if results and len(results) > 0:
            return parse_jamendo_track_raw(results[0])
        return None


async def get_fresh_track_url(jamendo_id: int) -> str:
    """
    Получает свежую ссылку на аудио с актуальным токеном.
    Возвращает прямой URL для стриминга.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{JAMENDO_BASE}/tracks/",
            params={
                "client_id": settings.JAMENDO_CLIENT_ID,
                "id": jamendo_id,
                "format": "json",
                "include": "musicinfo",
                "audioformat": "mp32"
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось получить ссылку от Jamendo"
            )
        
        data = response.json()
        results = data.get("results", [])
        
        if not results or len(results) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Трек не найден в каталоге Jamendo"
            )
        
        audio_url = results[0].get("audio")
        if not audio_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Jamendo не вернул audio_url"
            )
        
        return audio_url