# backend/app/integrations/lastfm_service.py
import httpx
import logging
from app.core.config import settings
from app.utils.genre_normalizer import normalize_genre

logger = logging.getLogger(__name__)
LASTFM_BASE = "http://ws.audioscrobbler.com/2.0/"

async def get_track_info(artist: str, track: str) -> dict:
    """
    Получает информацию о треке из Last.fm
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                LASTFM_BASE,
                params={
                    "method": "track.getInfo",
                    "artist": artist,
                    "track": track,
                    "api_key": settings.LASTFM_API_KEY,
                    "format": "json",
                    "autocorrect": "1"
                },
                timeout=10.0
            )
            
            logger.info(f"Last.fm response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Last.fm HTTP error: {response.status_code}")
                return {"genre": None, "tags": [], "similar_artists": []}
            
            data = response.json()
            
            # Проверяем наличие ошибки в ответе
            if "error" in data:
                error_code = data.get("error")
                error_msg = data.get("message", "Unknown error")
                logger.error(f"Last.fm API error {error_code}: {error_msg} for '{track} - {artist}'")
                
                # Если ошибка 11 (Service Offline) или 10 (Invalid API Key)
                if error_code in [10, 11]:
                    logger.critical(f"Last.fm service unavailable. Check API key and service status.")
                
                return {"genre": None, "tags": [], "similar_artists": []}
            
            track_info = data.get("track", {})
            if not track_info:
                logger.warning(f"No track info found for '{track} - {artist}'")
                return {"genre": None, "tags": [], "similar_artists": []}
            
            # Извлекаем теги
            tags = track_info.get("toptags", {}).get("tag", [])
            tag_names = [t["name"] for t in tags]
            
            # Нормализуем жанр
            genre = normalize_genre(tag_names)
            
            # Извлекаем похожих артистов
            similar = track_info.get("similar", {}).get("track", [])
            similar_artists = list(set([t["artist"]["name"] for t in similar[:5]]))
            
            logger.info(f"Last.fm found {len(tags)} tags for '{track} - {artist}', genre: {genre}")
            
            return {
                "genre": genre,
                "tags": tag_names[:10],
                "similar_artists": similar_artists
            }
            
    except httpx.TimeoutException:
        logger.error(f"Last.fm timeout for '{track} - {artist}'")
        return {"genre": None, "tags": [], "similar_artists": []}
    except Exception as e:
        logger.error(f"Last.fm track info error: {e}")
        return {"genre": None, "tags": [], "similar_artists": []}

async def get_artist_info(artist: str) -> dict:
    """
    Получает информацию об артисте (фолбэк)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                LASTFM_BASE,
                params={
                    "method": "artist.getTopTags",
                    "artist": artist,
                    "api_key": settings.LASTFM_API_KEY,
                    "format": "json",
                    "autocorrect": "1"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                return {"genre": None, "tags": []}
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"Last.fm artist error {data.get('error')}: {data.get('message')}")
                return {"genre": None, "tags": []}
            
            tags = data.get("toptags", {}).get("tag", [])
            tag_names = [t["name"] for t in tags]
            genre = normalize_genre(tag_names)
            
            return {
                "genre": genre,
                "tags": tag_names[:10]
            }
            
    except Exception as e:
        logger.error(f"Last.fm artist info error: {e}")
        return {"genre": None, "tags": []}

async def enrich_track_metadata(artist: str, track: str) -> dict:
    """
    Основная функция обогащения
    """
    logger.info(f"Starting enrichment for '{track} - {artist}'")
    
    # 1. Ищем трек
    track_data = await get_track_info(artist, track)
    if track_data["genre"]:
        logger.info(f"Enrichment success via track: genre={track_data['genre']}")
        return track_data
    
    # 2. Фолбэк на артиста
    logger.info(f"Track not found, falling back to artist '{artist}'")
    artist_data = await get_artist_info(artist)
    
    result = {
        "genre": artist_data["genre"],
        "tags": artist_data["tags"],
        "similar_artists": track_data["similar_artists"]
    }
    
    if result["genre"]:
        logger.info(f"Enrichment success via artist: genre={result['genre']}")
    else:
        logger.warning(f"Enrichment failed for '{track} - {artist}'")
    
    return result