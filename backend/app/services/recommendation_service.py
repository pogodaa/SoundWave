# backend/app/services/recommendation_service.py
"""
Content-Based рекомендации на основе лайков пользователя.

Алгоритм (ML, scikit-learn):
    1. Из таблицы user_likes загружаем треки, которые пользователь лайкнул.
    2. Строим текстовый профиль предпочтений: жанры и теги лайкнутых треков
       (жанры, встречающиеся чаще, дублируются — усиление веса в Bag-of-Words).
    3. Из БД выбираем кандидатов: is_available=True, не лайкнуты пользователем.
    4. Каждый кандидат описывается строкой «genre + tags».
    5. TfidfVectorizer (sklearn) превращает тексты в TF-IDF-векторы.
    6. cosine_similarity считает схожесть профиля пользователя с каждым кандидатом.
    7. Возвращаем top-N треков с наибольшей cosine similarity.

Edge cases:
    - 0 лайков → cold_start=True, пустой список (фронт просит лайкать треки).
    - Лайки без жанров и тегов → fallback на популярные треки.
"""
import logging
from collections import Counter
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.models.artist import Artist
from app.models.track import Track
from app.models.user_like import UserLike
from app.schemas.recommendations import PersonalRecommendationsResponse
from app.schemas.track import TrackRead
from app.services.interaction_service import _track_to_trackread
from app.services.track_service import get_popular_with_cache

logger = logging.getLogger(__name__)

RECOMMENDATION_CANDIDATE_POOL = 400
DEFAULT_LIMIT = 20


def _normalize_token(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _track_feature_tokens(track: Track) -> list[str]:
    """Извлекает токены жанра и тегов для ML-профиля."""
    tokens: list[str] = []
    if track.genre:
        tokens.append(_normalize_token(track.genre))
    if track.tags:
        for tag in track.tags:
            if tag:
                tokens.append(_normalize_token(tag))
    return tokens


def _track_feature_text(track: Track) -> str:
    """Текстовое описание трека для TF-IDF (genre + tags)."""
    tokens = _track_feature_tokens(track)
    return " ".join(tokens) if tokens else ""


def _build_user_profile_document(liked_tracks: list[Track]) -> str:
    """
    Профиль пользователя: частоты жанров/тегов из лайков.
    Повторение токена пропорционально частоте — простой вес предпочтений.
    """
    counter: Counter[str] = Counter()
    for track in liked_tracks:
        counter.update(_track_feature_tokens(track))

    if not counter:
        return ""

    weighted_tokens: list[str] = []
    for token, count in counter.items():
        weighted_tokens.extend([token] * count)
    return " ".join(weighted_tokens)


def _rank_candidates_by_similarity(
    user_profile_doc: str,
    candidates: list[tuple[Track, Optional[str]]],
) -> list[tuple[float, Track, Optional[str]]]:
    """
    Ранжирует кандидатов по cosine similarity (TF-IDF + sklearn).
    Возвращает список (score, track, artist_name), отсортированный по убыванию score.
    """
    if not user_profile_doc or not candidates:
        return []

    candidate_docs = [_track_feature_text(track) for track, _ in candidates]
    # Кандидаты без описания получают минимальный приоритет, но не отбрасываются
    candidate_docs = [doc if doc else "unknown" for doc in candidate_docs]

    corpus = [user_profile_doc] + candidate_docs
    vectorizer = TfidfVectorizer(min_df=1, token_pattern=r"(?u)\b[\w\-]+\b")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    ranked: list[tuple[float, Track, Optional[str]]] = []
    for idx, (track, artist_name) in enumerate(candidates):
        ranked.append((float(similarity_scores[idx]), track, artist_name))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


async def _load_liked_tracks(db: AsyncSession, user_id: int) -> list[tuple[Track, Optional[str]]]:
    """Лайкнутые треки пользователя с именем исполнителя."""
    stmt = (
        select(Track, Artist.name.label("artist_name"))
        .join(UserLike, UserLike.track_id == Track.id)
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(UserLike.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.all()


async def _load_liked_track_ids(db: AsyncSession, user_id: int) -> set[int]:
    stmt = select(UserLike.track_id).where(UserLike.user_id == user_id)
    result = await db.execute(stmt)
    return set(result.scalars().all())


async def _load_candidate_tracks(
    db: AsyncSession,
    user_id: int,
    pool_size: int,
) -> list[tuple[Track, Optional[str]]]:
    """Кандидаты для рекомендаций: доступные, одобренные, ещё не лайкнутые."""
    liked_ids_subq = select(UserLike.track_id).where(UserLike.user_id == user_id)

    stmt = (
        select(Track, Artist.name.label("artist_name"))
        .join(Artist, Track.artist_id == Artist.id, isouter=True)
        .where(Track.is_available.is_(True))
        .where(Track.moderation_status == "approved")
        .where(Track.id.notin_(liked_ids_subq))
        .limit(pool_size)
    )
    result = await db.execute(stmt)
    return result.all()


async def _popular_fallback(
    db: AsyncSession,
    user_id: int,
    limit: int,
    background_tasks: Optional[BackgroundTasks],
) -> PersonalRecommendationsResponse:
    """Популярные треки, исключая уже лайкнутые (если ML-профиль построить нельзя)."""
    liked_ids = await _load_liked_track_ids(db, user_id)
    popular_raw = await get_popular_with_cache(
        db,
        limit=limit + len(liked_ids),
        background_tasks=background_tasks,
    )

    tracks: list[TrackRead] = []
    for item in popular_raw:
        track_id = item.get("id")
        if track_id is None or track_id in liked_ids:
            continue
        tracks.append(TrackRead(**item))
        if len(tracks) >= limit:
            break

    logger.info(
        f"[ML] Fallback на популярные для user_id={user_id}: {len(tracks)} треков"
    )
    return PersonalRecommendationsResponse(
        tracks=tracks,
        cold_start=False,
        used_popular_fallback=True,
    )


async def get_personal_recommendations(
    db: AsyncSession,
    user_id: int,
    limit: int = DEFAULT_LIMIT,
    background_tasks: Optional[BackgroundTasks] = None,
) -> PersonalRecommendationsResponse:
    """
    Персональные рекомендации: Content-Based Filtering по лайкам.
    """
    liked_rows = await _load_liked_tracks(db, user_id)

    if not liked_rows:
        logger.info(f"[ML] Холодный старт для user_id={user_id}: 0 лайков")
        return PersonalRecommendationsResponse(tracks=[], cold_start=True)

    liked_tracks = [track for track, _ in liked_rows]
    user_profile_doc = _build_user_profile_document(liked_tracks)

    if not user_profile_doc.strip():
        logger.info(
            f"[ML] У user_id={user_id} есть лайки, но нет жанров/тегов — fallback на популярные"
        )
        return await _popular_fallback(db, user_id, limit, background_tasks)

    candidates = await _load_candidate_tracks(db, user_id, RECOMMENDATION_CANDIDATE_POOL)
    if not candidates:
        logger.warning(f"[ML] Нет кандидатов для user_id={user_id}, fallback на популярные")
        return await _popular_fallback(db, user_id, limit, background_tasks)

    ranked = _rank_candidates_by_similarity(user_profile_doc, candidates)

    tracks: list[TrackRead] = []
    for score, track, artist_name in ranked:
        if score <= 0 and tracks:
            # Остальные с нулевой схожестью не добавляем после первых релевантных
            break
        tracks.append(_track_to_trackread(track, artist_name))
        if len(tracks) >= limit:
            break

    if len(tracks) < limit:
        # Добираем популярными, если ML нашёл мало
        liked_ids = await _load_liked_track_ids(db, user_id)
        existing_ids = liked_ids | {t.id for t in tracks if t.id is not None}
        popular_raw = await get_popular_with_cache(
            db,
            limit=limit * 2,
            background_tasks=background_tasks,
        )
        for item in popular_raw:
            track_id = item.get("id")
            if track_id is None or track_id in existing_ids:
                continue
            tracks.append(TrackRead(**item))
            existing_ids.add(track_id)
            if len(tracks) >= limit:
                break

    top_score = ranked[0][0] if ranked else 0.0
    logger.info(
        f"[ML] Рекомендации для user_id={user_id}: {len(tracks)} треков, "
        f"лайков={len(liked_rows)}, max cosine={top_score:.4f}"
    )

    return PersonalRecommendationsResponse(
        tracks=tracks[:limit],
        cold_start=False,
        used_popular_fallback=False,
    )
