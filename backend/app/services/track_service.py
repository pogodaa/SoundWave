# backend/app/services/track_service.py
import logging
from typing import Optional, List
import asyncio
from asyncio import Semaphore
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status

from app.models.track import Track
from app.models.artist import Artist
from app.db.session import AsyncSessionLocal
from app.integrations.jamendo_service import (
    get_random_tracks,
    fetch_track_by_id,
    get_fresh_track_url,
    search_tracks
)
from app.integrations.lastfm_service import enrich_track_metadata
from app.utils.genre_from_name import extract_genre_from_name
from app.utils.keyword_genre_classifier import classify_genre_by_keywords, get_confidence_score
import httpx

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6          # сколько часов считаем ссылку свежей
POOL_SIZE = 50               # размер внутреннего пула треков


async def _enrich_genre_async(jamendo_id: int, artist_name: str, track_title: str):
    """Фоновая задача обогащения жанра трека."""
    try:
        enriched_data = await enrich_track_metadata(artist=artist_name, track=track_title)
        final_genre = enriched_data.get("genre") if enriched_data else None
        final_tags = enriched_data.get("tags", []) if enriched_data else []

        if not final_genre:
            keyword_genre = classify_genre_by_keywords(title=track_title, artist=artist_name)
            if keyword_genre:
                confidence = get_confidence_score(keyword_genre, track_title, artist_name)
                logger.info(f"Классификатор: '{track_title}' -> '{keyword_genre}' (уверенность: {confidence:.1f})")
                final_genre = keyword_genre

        if final_genre:
            async with AsyncSessionLocal() as bg_session:
                stmt = (
                    update(Track)
                    .where(Track.jamendo_id == jamendo_id)
                    .values(
                        genre=final_genre,
                        tags=final_tags if final_tags else None,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                await bg_session.execute(stmt)
                await bg_session.commit()
                logger.info(f"Жанр обновлён для трека {jamendo_id}: genre='{final_genre}'")
    except Exception as e:
        logger.warning(f"Ошибка обогащения жанра для '{track_title}': {e}")


async def search_tracks_with_cache(
    db: AsyncSession,
    query: str,
    limit: int,
    background_tasks: BackgroundTasks
) -> list[dict]:
    """Поиск треков с кэшированием."""
    search_terms = query.split()
    conditions = []
    for term in search_terms:
        conditions.append(Track.title.ilike(f"%{term}%"))
        conditions.append(Artist.name.ilike(f"%{term}%"))

    stmt = (
        select(Track, Artist.name.label("artist_name_for_response"))
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(or_(*conditions))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    db_tracks = []
    for track, artist_name in rows:
        track_dict = {
            "id": track.id,
            "jamendo_id": track.jamendo_id,
            "title": track.title,
            "artist_name": artist_name or "Неизвестный исполнитель",
            "album_name": None,
            "duration": track.duration,
            "genre": track.genre,
            "tags": track.tags or [],
            "audio_url": track.audio_url,
            "cover_url": track.image_url or "/covers/default.png",
            "releasedate": None,
            "is_user_uploaded": track.is_user_uploaded,
            "created_at": track.added_at,
            "updated_at": track.updated_at,
            "is_available": track.is_available,
        }
        db_tracks.append(track_dict)

    if len(db_tracks) >= limit:
        logger.info(f"Найдено {len(db_tracks)} треков в БД (кэш)")
        return db_tracks

    remaining = limit - len(db_tracks)
    fetch_limit = int(remaining * 1.5)
    logger.info(f"В БД только {len(db_tracks)} треков, запрашиваем ещё {fetch_limit} у Jamendo")

    try:
        jamendo_data = await search_tracks(query, fetch_limit)
    except Exception as e:
        logger.error(f"Ошибка при поиске треков: {e}")
        return db_tracks

    if jamendo_data:
        await _upsert_tracks(db, jamendo_data)
        for t in jamendo_data:
            background_tasks.add_task(
                _enrich_genre_async,
                jamendo_id=int(t["id"]),
                artist_name=t.get("artist_name", "Unknown"),
                track_title=t["title"]
            )

    return db_tracks[:limit]


def _track_to_response_dict(track: Track, artist_name: Optional[str]) -> dict:
    """Преобразует ORM-модель Track в словарь ответа API."""
    return {
        "id": track.id,
        "jamendo_id": track.jamendo_id,
        "title": track.title,
        "artist_name": artist_name or "Неизвестный исполнитель",
        "duration": track.duration,
        "genre": track.genre,
        "tags": track.tags or [],
        "audio_url": track.audio_url,
        "cover_url": track.image_url or "/covers/default.png",
        "is_user_uploaded": track.is_user_uploaded,
        "created_at": track.added_at,
        "updated_at": track.updated_at,
        "is_available": track.is_available,
    }


def _is_track_url_fresh(track: Track, now: datetime) -> bool:
    """Проверяет, актуальна ли кэшированная ссылка на воспроизведение."""
    last_updated = track.play_url_updated_at or track.added_at
    return (now - last_updated) < timedelta(hours=CACHE_TTL_HOURS)


async def _select_random_tracks(
    db: AsyncSession,
    limit: int,
    exclude_ids: set[int],
) -> list[tuple[Track, Optional[str]]]:
    """
    Выбирает случайные Jamendo-треки из БД.

    Args:
        db: Асинхронная сессия БД.
        limit: Сколько треков выбрать.
        exclude_ids: ID треков, которые нельзя включать в выборку.
    """
    stmt = (
        select(Track, Artist.name.label("artist_name_for_response"))
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(Track.jamendo_id.isnot(None))
        .where(Track.is_available.is_(True))
    )
    if exclude_ids:
        stmt = stmt.where(Track.id.notin_(exclude_ids))
    stmt = stmt.order_by(func.random()).limit(limit)
    result = await db.execute(stmt)
    return result.all()


async def _load_tracks_with_artists(
    db: AsyncSession,
    track_ids: List[int],
) -> list[tuple[Track, Optional[str]]]:
    """Загружает треки по списку ID вместе с именами артистов."""
    if not track_ids:
        return []
    stmt = (
        select(Track, Artist.name.label("artist_name_for_response"))
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(Track.id.in_(track_ids))
    )
    result = await db.execute(stmt)
    return result.all()


async def _refresh_stale_tracks(
    db: AsyncSession,
    tracks: List[Track],
    now: datetime,
) -> List[int]:
    """
    Параллельно обновляет устаревшие audio_url у переданных треков.

    Returns:
        Список ID треков, для которых обновление ссылки не удалось.
    """
    if not tracks:
        return []

    logger.info(f"Обновляем {len(tracks)} устаревших ссылок")
    semaphore = Semaphore(5)
    track_by_id = {track.id: track for track in tracks}

    async def refresh_one(track: Track) -> tuple[int, bool, Optional[str]]:
        async with semaphore:
            try:
                fresh_url = await get_fresh_track_url(track.jamendo_id)
                logger.info(f"Ссылка обновлена для трека {track.jamendo_id}")
                return track.id, True, fresh_url
            except Exception as e:
                logger.warning(
                    f"Не удалось обновить ссылку для трека {track.jamendo_id}: {e}"
                )
                return track.id, False, None

    results = await asyncio.gather(*(refresh_one(track) for track in tracks))

    has_updates = False
    failed_ids: List[int] = []
    for track_id, success, fresh_url in results:
        if success and fresh_url is not None:
            track = track_by_id[track_id]
            track.audio_url = fresh_url
            track.play_url_updated_at = now
            track.is_available = True
            track.updated_at = now
            has_updates = True
        else:
            failed_ids.append(track_id)

    if has_updates:
        await db.commit()

    return failed_ids


async def _handle_broken_tracks(
    db: AsyncSession,
    failed_track_ids: List[int],
) -> None:
    """
    Обрабатывает треки с битой ссылкой после неудачного обновления audio_url у Jamendo.

    Физическое удаление из БД не выполняется (во избежание ошибок FK на лайки и связанные сущности):
    всем таким записям выставляется is_available = False.
    """
    if not failed_track_ids:
        return

    now = datetime.now(timezone.utc)
    for track_id in failed_track_ids:
        await db.execute(
            update(Track)
            .where(Track.id == track_id)
            .values(is_available=False, updated_at=now),
        )
        logger.info(f"Трек {track_id} помечен как недоступный (Jamendo не отдал актуальный audio_url)")
    await db.commit()


async def _supplement_tracks_from_jamendo(
    db: AsyncSession,
    count: int,
) -> int:
    """
    Дозапрашивает треки у Jamendo и сохраняет их в БД.

    Returns:
        Количество успешно сохранённых треков.
    """
    if count <= 0:
        return 0

    max_per_request = 10
    saved_total = 0

    while saved_total < count:
        fetch_count = min(count - saved_total, max_per_request)
        try:
            new_tracks = await get_random_tracks(fetch_count)
            if not new_tracks:
                logger.warning("Jamendo не вернул новые треки для пополнения пула")
                break

            await _upsert_tracks(db, new_tracks)
            saved_total += len(new_tracks)
            logger.info(f"Добавлено {len(new_tracks)} новых треков из Jamendo")
        except Exception as e:
            logger.error(f"Ошибка при запросе дополнительных треков у Jamendo: {e}")
            break

    return saved_total


async def get_popular_with_cache(
    db: AsyncSession,
    limit: int = 20,
    background_tasks: BackgroundTasks = None,
) -> list[dict]:
    """
    Возвращает популярные треки с кэшированием и обработкой битых ссылок.

    Алгоритм:
        1. Набираем limit случайных **доступных** (is_available=True) треков из БД.
        2. Для треков с устаревшей ссылкой запрашиваем свежий audio_url у Jamendo.
        3. При ошибке обновления трек остаётся в БД с is_available = False и не попадает в ответ.
        4. При нехватке треков в БД дозапрашиваем новые у Jamendo.

    Args:
        db: Асинхронная сессия БД.
        limit: Требуемое количество треков в ответе.
        background_tasks: Зарезервировано для фоновых задач (не используется).

    Returns:
        Список словарей треков длиной до limit элементов.
    """
    now = datetime.now(timezone.utc)
    popular_tracks: List[dict] = []
    included_ids: set[int] = set()
    max_iterations = 15
    iteration = 0

    while len(popular_tracks) < limit and iteration < max_iterations:
        iteration += 1
        needed = limit - len(popular_tracks)
        selection_exclude = included_ids

        rows = await _select_random_tracks(db, needed, selection_exclude)

        if not rows:
            logger.info(
                f"В БД не хватает кандидатов ({len(popular_tracks)}/{limit}), "
                f"запрашиваем {needed} треков у Jamendo"
            )
            added = await _supplement_tracks_from_jamendo(db, needed)
            if added == 0:
                logger.warning(
                    f"Не удалось пополнить пул треков: возвращаем {len(popular_tracks)}/{limit}"
                )
                break
            continue

        fresh_rows: list[tuple[Track, Optional[str]]] = []
        stale_tracks: List[Track] = []

        for track, artist_name in rows:
            if _is_track_url_fresh(track, now):
                fresh_rows.append((track, artist_name))
            else:
                stale_tracks.append(track)

        for track, artist_name in fresh_rows:
            if track.id in included_ids:
                continue
            popular_tracks.append(_track_to_response_dict(track, artist_name))
            included_ids.add(track.id)

        if stale_tracks:
            failed_ids = await _refresh_stale_tracks(db, stale_tracks, now)
            await _handle_broken_tracks(db, failed_ids)

            surviving_stale_ids = [track.id for track in stale_tracks]
            reloaded_rows = await _load_tracks_with_artists(db, surviving_stale_ids)

            for track, artist_name in reloaded_rows:
                if track.id in included_ids:
                    continue
                if not track.is_available:
                    continue
                popular_tracks.append(_track_to_response_dict(track, artist_name))
                included_ids.add(track.id)

        if len(popular_tracks) < limit and len(rows) < needed:
            shortfall = needed - len(rows)
            if shortfall > 0:
                await _supplement_tracks_from_jamendo(db, shortfall)

    if len(popular_tracks) < limit:
        logger.warning(
            f"Не удалось набрать ровно {limit} треков: возвращаем {len(popular_tracks)}"
        )
    else:
        logger.info(f"Возвращаем {limit} популярных треков")

    return popular_tracks[:limit]


async def _upsert_tracks(db: AsyncSession, tracks_data: list[dict]):
    """UPSERT треков с установкой is_available = True."""
    now = datetime.now(timezone.utc)
    saved_count = 0

    for t in tracks_data:
        try:
            if not t.get("id") or not t.get("title") or not t.get("audio_url"):
                continue

            artist_name = t.get("artist_name") or "Неизвестный исполнитель"
            stmt = select(Artist).where(Artist.name == artist_name)
            res = await db.execute(stmt)
            artist = res.scalar_one_or_none()
            if not artist:
                artist = Artist(name=artist_name, image_url=t.get("image_url"))
                db.add(artist)
                await db.flush()

            tags = t.get("tags") or []
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif not isinstance(tags, list):
                tags = []

            upsert_stmt = pg_insert(Track).values(
                jamendo_id=int(t["id"]),
                title=str(t["title"])[:255],
                artist_id=artist.id,
                duration=int(t.get("duration") or 0),
                audio_url=str(t["audio_url"]),
                image_url=str(t.get("image_url")) if t.get("image_url") else None,
                genre=tags[0] if tags else None,
                tags=tags,
                is_user_uploaded=False,
                moderation_status="approved",
                added_at=now,
                updated_at=now,
                play_url_updated_at=now,
                is_available=True
            ).on_conflict_do_update(
                index_elements=["jamendo_id"],
                set_={
                    "title": str(t["title"])[:255],
                    "duration": int(t.get("duration") or 0),
                    "audio_url": str(t["audio_url"]),
                    "image_url": str(t.get("image_url")) if t.get("image_url") else None,
                    "genre": tags[0] if tags else None,
                    "tags": tags,
                    "updated_at": now,
                    "play_url_updated_at": now,
                    "is_available": True
                }
            )
            await db.execute(upsert_stmt)
            saved_count += 1

        except Exception as e:
            logger.warning(f"Ошибка при сохранении трека {t.get('id')}: {e}")
            continue

    await db.commit()
    logger.info(f"Закешировано {saved_count} треков из Jamendo")


async def get_fresh_play_url(db: AsyncSession, track_id: int) -> str:
    """
    Возвращает актуальную прямую ссылку для воспроизведения.
    При успешном обновлении устанавливает is_available = True.
    """
    stmt = select(Track).where(Track.id == track_id)
    result = await db.execute(stmt)
    track = result.scalar_one_or_none()

    if not track or not track.jamendo_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Трек не найден в базе"
        )

    now = datetime.now(timezone.utc)
    last_updated = track.play_url_updated_at or track.added_at
    token_expired = (now - last_updated) > timedelta(hours=CACHE_TTL_HOURS)

    if not token_expired:
        logger.info(f"[КЭШ] Трек {track_id}: ссылка актуальна (обновлена {last_updated}), использую из БД")
        return track.audio_url

    logger.info(f"[API] Трек {track_id}: ссылка устарела, запрашиваю новую у Jamendo API")
    try:
        fresh_data = await fetch_track_by_id(track.jamendo_id)
        if not fresh_data or not fresh_data.get("audio_url"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Jamendo не вернул актуальные данные"
            )

        tags = fresh_data.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif not isinstance(tags, list):
            tags = []

        upsert_stmt = pg_insert(Track).values(
            jamendo_id=track.jamendo_id,
            title=str(fresh_data["title"])[:255],
            artist_id=track.artist_id,
            duration=int(fresh_data.get("duration") or track.duration or 0),
            audio_url=str(fresh_data["audio_url"]),
            image_url=str(fresh_data.get("image_url")) if fresh_data.get("image_url") else track.image_url,
            genre=tags[0] if tags else track.genre,
            tags=tags if tags else track.tags,
            is_user_uploaded=False,
            moderation_status="approved",
            added_at=track.added_at or now,
            updated_at=now,
            play_url_updated_at=now,
            is_available=True
        ).on_conflict_do_update(
            index_elements=["jamendo_id"],
            set_={
                "title": str(fresh_data["title"])[:255],
                "duration": int(fresh_data.get("duration") or track.duration or 0),
                "audio_url": str(fresh_data["audio_url"]),
                "image_url": str(fresh_data.get("image_url")) if fresh_data.get("image_url") else track.image_url,
                "genre": tags[0] if tags else track.genre,
                "tags": tags if tags else track.tags,
                "updated_at": now,
                "play_url_updated_at": now,
                "is_available": True
            }
        )
        await db.execute(upsert_stmt)
        await db.commit()
        logger.info(f"Ссылка обновлена для трека {track_id}")

        return fresh_data["audio_url"]

    except httpx.ReadTimeout:
        logger.warning(f"Таймаут при обновлении ссылки для трека {track_id}, возвращаем кэшированную")
        return track.audio_url
    except httpx.HTTPError as e:
        logger.error(f"HTTP ошибка при обновлении ссылки для трека {track_id}: {e}")
        return track.audio_url
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Не удалось обновить ссылку для трека {track_id}: {e}")
        return track.audio_url