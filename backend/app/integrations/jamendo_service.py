# backend/app/integrations/jamendo_service.py
import asyncio
import httpx
import logging
from app.core.config import settings
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

JAMENDO_BASE = "https://api.jamendo.com/v3.0"
REQUIRED_FIELDS = ["id", "name", "audio"]
JAMENDO_SEARCH_TIMEOUT = 30.0
JAMENDO_SEARCH_MAX_RETRIES = 3


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


def _merge_parsed_tracks(
    target: list[dict],
    seen_ids: set[int],
    raw_results: list[dict],
    max_count: int,
) -> None:
    """Добавляет валидные треки в target без дублей по id."""
    for t in raw_results:
        if len(target) >= max_count:
            return
        parsed = parse_jamendo_track_raw(t)
        if not parsed:
            continue
        track_id = parsed["id"]
        if track_id in seen_ids:
            continue
        seen_ids.add(track_id)
        target.append(parsed)


async def _jamendo_tracks_request(
    client: httpx.AsyncClient,
    extra_params: dict,
    fetch_limit: int,
    log_label: str,
) -> list[dict]:
    """Один HTTP-запрос к /tracks/ с повторами при таймаутах и 5xx."""
    if not settings.JAMENDO_CLIENT_ID:
        logger.error("[Jamendo] JAMENDO_CLIENT_ID не задан — поиск невозможен")
        return []

    params = {
        "client_id": settings.JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": fetch_limit,
        "include": "musicinfo",
        "audioformat": "mp32",
        **extra_params,
    }
    last_error: Optional[Exception] = None

    for attempt in range(1, JAMENDO_SEARCH_MAX_RETRIES + 1):
        try:
            response = await client.get(
                f"{JAMENDO_BASE}/tracks/",
                params=params,
                timeout=httpx.Timeout(JAMENDO_SEARCH_TIMEOUT, connect=10.0),
            )
            if response.status_code != 200:
                logger.warning(
                    f"[Jamendo] {log_label}: HTTP {response.status_code} "
                    f"(попытка {attempt}/{JAMENDO_SEARCH_MAX_RETRIES})"
                )
                if response.status_code >= 500 and attempt < JAMENDO_SEARCH_MAX_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
                    continue
                return []

            payload = response.json()
            if not isinstance(payload, dict):
                logger.error(f"[Jamendo] {log_label}: ответ не JSON-объект")
                return []

            headers = payload.get("headers") or {}
            if headers.get("status") == "failed":
                logger.error(f"[Jamendo] {log_label}: API status=failed, headers={headers}")
                return []

            results = payload.get("results")
            if not isinstance(results, list):
                logger.warning(f"[Jamendo] {log_label}: поле results отсутствует или не список")
                return []

            logger.info(
                f"[Jamendo] {log_label}: получено {len(results)} сырых треков "
                f"(попытка {attempt})"
            )
            return results

        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            last_error = e
            logger.warning(
                f"[Jamendo] {log_label}: сеть/таймаут ({type(e).__name__}: {e}), "
                f"попытка {attempt}/{JAMENDO_SEARCH_MAX_RETRIES}"
            )
            if attempt < JAMENDO_SEARCH_MAX_RETRIES:
                await asyncio.sleep(0.5 * attempt)
        except httpx.HTTPError as e:
            last_error = e
            logger.error(f"[Jamendo] {log_label}: HTTPError {type(e).__name__}: {e}")
            break
        except ValueError as e:
            last_error = e
            logger.error(f"[Jamendo] {log_label}: ошибка разбора JSON: {e}")
            break

    if last_error:
        logger.error(
            f"[Jamendo] {log_label}: запрос не удался после {JAMENDO_SEARCH_MAX_RETRIES} попыток: "
            f"{type(last_error).__name__}: {last_error}"
        )
    return []


async def search_tracks(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Поиск треков: namesearch, при нехватке результатов — дополнение по тегу (tags).
    Устойчив к таймаутам и временным ошибкам API.
    """
    fetch_limit = max(limit, 50)
    search_query = query.strip()
    if not search_query:
        return []

    valid: list[dict] = []
    seen_ids: set[int] = set()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        raw_namesearch = await _jamendo_tracks_request(
            client,
            {"namesearch": search_query},
            fetch_limit,
            f"namesearch «{search_query}»",
        )
        _merge_parsed_tracks(valid, seen_ids, raw_namesearch, fetch_limit)

        # Для жанровых запросов (pop, jazz, …) namesearch может дать мало — добираем по тегу
        if len(valid) < fetch_limit:
            raw_tags = await _jamendo_tracks_request(
                client,
                {"tags": search_query},
                fetch_limit,
                f"tags «{search_query}»",
            )
            before = len(valid)
            _merge_parsed_tracks(valid, seen_ids, raw_tags, fetch_limit)
            if len(valid) > before:
                logger.info(
                    f"[Jamendo] Поиск «{search_query}»: +{len(valid) - before} треков по тегу "
                    f"(всего {len(valid)})"
                )

    logger.info(f"[Jamendo] Поиск «{search_query}»: итого {len(valid)} валидных треков")
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