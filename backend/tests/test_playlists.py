# backend/tests/test_playlists.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.track import Track
from app.models.artist import Artist
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.core.security import create_access_token, get_password_hash


pytestmark = pytest.mark.asyncio


class TestPlaylistCRUD:
    """Тесты основного CRUD для плейлистов"""

    async def test_create_playlist_public(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Создание публичного плейлиста"""
        token = create_access_token(test_user.id)

        payload = {
            "name": "Тестовый плейлист",
            "description": "Описание для теста",
            "is_public": True
        }

        response = await async_client.post(
            "/api/v1/playlists",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["is_public"] is True
        assert data["user_id"] == test_user.id
        assert data["share_token"] is not None
        assert len(data["tracks"]) == 0

    async def test_create_playlist_private(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Создание приватного плейлиста (share_token должен быть null)"""
        token = create_access_token(test_user.id)

        payload = {
            "name": "Личный плейлист",
            "is_public": False
        }

        response = await async_client.post(
            "/api/v1/playlists",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_public"] is False
        assert data["share_token"] is None

    async def test_get_user_playlists(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Получение списка плейлистов пользователя"""
        token = create_access_token(test_user.id)

        # Создаём тестовые плейлисты
        for i in range(3):
            playlist = Playlist(
                user_id=test_user.id,
                name=f"Плейлист {i}",
                is_public=True
            )
            db_session.add(playlist)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/playlists",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(p["user_id"] == test_user.id for p in data)

    async def test_get_playlist_by_id(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Получение конкретного плейлиста с треками"""
        token = create_access_token(test_user.id)

        # Создаём плейлист
        playlist = Playlist(
            user_id=test_user.id,
            name="Плейлист с треками",
            is_public=True
        )
        db_session.add(playlist)
        await db_session.commit()
        await db_session.refresh(playlist)

        # Создаём и добавляем трек
        track = Track(
            jamendo_id=999,
            title="Тестовый трек",
            artist_id=test_artist.id,
            duration=180,
            audio_url="https://example.com/track.mp3",
            image_url="https://example.com/cover.jpg",
            genre="Pop"
        )
        db_session.add(track)
        await db_session.commit()
        await db_session.refresh(track)

        playlist_track = PlaylistTrack(
            playlist_id=playlist.id,
            track_id=track.id,
            position=1
        )
        db_session.add(playlist_track)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/playlists/{playlist.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == playlist.id
        assert len(data["tracks"]) == 1
        assert data["tracks"][0]["track_id"] == track.id
        assert data["tracks"][0]["title"] == track.title

    async def test_update_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Обновление плейлиста и смена приватности"""
        token = create_access_token(test_user.id)

        playlist = Playlist(
            user_id=test_user.id,
            name="Старое название",
            description="Старое описание",
            is_public=True,
            share_token="old_token_123"
        )
        db_session.add(playlist)
        await db_session.commit()

        payload = {
            "name": "Новое название",
            "is_public": False
        }

        response = await async_client.patch(
            f"/api/v1/playlists/{playlist.id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Новое название"
        assert data["description"] == "Старое описание"
        assert data["is_public"] is False
        assert data["share_token"] is None

    async def test_delete_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Удаление плейлиста"""
        token = create_access_token(test_user.id)

        playlist = Playlist(
            user_id=test_user.id,
            name="Плейлист для удаления",
            is_public=True
        )
        db_session.add(playlist)
        await db_session.commit()

        response = await async_client.delete(
            f"/api/v1/playlists/{playlist.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Проверяем, что плейлист действительно удалён
        result = await db_session.execute(
            select(Playlist).where(Playlist.id == playlist.id)
        )
        assert result.scalar_one_or_none() is None


class TestPlaylistTracks:
    """Тесты управления треками в плейлистах"""

    async def test_add_track_to_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Добавление трека в плейлист"""
        token = create_access_token(test_user.id)

        # Создаём плейлист и трек
        playlist = Playlist(user_id=test_user.id, name="Test", is_public=True)
        track = Track(
            jamendo_id=998,
            title="Test Track",
            artist_id=test_artist.id,
            duration=200,
            audio_url="https://example.com/t.mp3"
        )
        db_session.add_all([playlist, track])
        await db_session.commit()
        await db_session.refresh(playlist)
        await db_session.refresh(track)

        payload = {"track_id": track.id, "position": 1}

        response = await async_client.post(
            f"/api/v1/playlists/{playlist.id}/tracks",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tracks"]) == 1
        assert data["tracks"][0]["track_id"] == track.id
        assert data["tracks"][0]["position"] == 1

    async def test_add_duplicate_track(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Попытка добавить уже существующий трек"""
        token = create_access_token(test_user.id)

        playlist = Playlist(user_id=test_user.id, name="Test", is_public=True)
        track = Track(
            jamendo_id=997,
            title="Duplicate Track",
            artist_id=test_artist.id,
            duration=150,
            audio_url="https://example.com/dup.mp3"
        )
        db_session.add_all([playlist, track])
        await db_session.commit()
        await db_session.refresh(playlist)
        await db_session.refresh(track)

        # Добавляем трек первый раз
        pt = PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=1)
        db_session.add(pt)
        await db_session.commit()

        # Пытаемся добавить повторно
        payload = {"track_id": track.id, "position": 2}
        response = await async_client.post(
            f"/api/v1/playlists/{playlist.id}/tracks",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "уже в плейлисте" in response.json()["detail"]

    async def test_add_track_with_position_shift(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Добавление трека с автоматическим сдвигом позиций"""
        token = create_access_token(test_user.id)

        playlist = Playlist(user_id=test_user.id, name="Reorder Test", is_public=True)
        track1 = Track(jamendo_id=996, title="Track 1", artist_id=test_artist.id, duration=100, audio_url="https://example.com/1.mp3")
        track2 = Track(jamendo_id=995, title="Track 2", artist_id=test_artist.id, duration=100, audio_url="https://example.com/2.mp3")
        track3 = Track(jamendo_id=994, title="Track 3", artist_id=test_artist.id, duration=100, audio_url="https://example.com/3.mp3")
        
        db_session.add_all([playlist, track1, track2, track3])
        await db_session.commit()
        await db_session.refresh(playlist)

        # Добавляем два трека
        db_session.add_all([
            PlaylistTrack(playlist_id=playlist.id, track_id=track1.id, position=1),
            PlaylistTrack(playlist_id=playlist.id, track_id=track2.id, position=2)
        ])
        await db_session.commit()

        # Добавляем третий трек на позицию 1 (должен сдвинуть остальные)
        payload = {"track_id": track3.id, "position": 1}
        response = await async_client.post(
            f"/api/v1/playlists/{playlist.id}/tracks",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        tracks = data["tracks"]
        
        # Проверяем порядок: track3 на позиции 1, остальные сдвинуты
        assert tracks[0]["track_id"] == track3.id and tracks[0]["position"] == 1
        assert tracks[1]["track_id"] == track1.id and tracks[1]["position"] == 2
        assert tracks[2]["track_id"] == track2.id and tracks[2]["position"] == 3

    async def test_remove_track_from_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Удаление трека из плейлиста (связь, не сам трек)"""
        token = create_access_token(test_user.id)

        playlist = Playlist(user_id=test_user.id, name="Test", is_public=True)
        track = Track(
            jamendo_id=993,
            title="To Remove",
            artist_id=test_artist.id,
            duration=180,
            audio_url="https://example.com/remove.mp3"
        )
        db_session.add_all([playlist, track])
        await db_session.commit()
        await db_session.refresh(playlist)
        await db_session.refresh(track)

        # Создаём связь
        pt = PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=1)
        db_session.add(pt)
        await db_session.commit()

        # Удаляем связь
        response = await async_client.delete(
            f"/api/v1/playlists/{playlist.id}/tracks/{track.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Проверяем, что связь удалена
        result = await db_session.execute(
            select(PlaylistTrack).where(
                PlaylistTrack.playlist_id == playlist.id,
                PlaylistTrack.track_id == track.id
            )
        )
        assert result.scalar_one_or_none() is None

        # Проверяем, что сам трек остался в БД
        track_result = await db_session.execute(
            select(Track).where(Track.id == track.id)
        )
        assert track_result.scalar_one_or_none() is not None

    async def test_reorder_tracks(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_artist: Artist,
        db_session: AsyncSession
    ):
        """Изменение порядка треков"""
        token = create_access_token(test_user.id)

        playlist = Playlist(user_id=test_user.id, name="Reorder", is_public=True)
        track1 = Track(jamendo_id=992, title="T1", artist_id=test_artist.id, duration=100, audio_url="https://example.com/t1.mp3")
        track2 = Track(jamendo_id=991, title="T2", artist_id=test_artist.id, duration=100, audio_url="https://example.com/t2.mp3")
        
        db_session.add_all([playlist, track1, track2])
        await db_session.commit()
        await db_session.refresh(playlist)

        # Добавляем треки
        db_session.add_all([
            PlaylistTrack(playlist_id=playlist.id, track_id=track1.id, position=1),
            PlaylistTrack(playlist_id=playlist.id, track_id=track2.id, position=2)
        ])
        await db_session.commit()

        # Меняем порядок: track1 -> 2, track2 -> 1
        payload = {"track_positions": {str(track1.id): 2, str(track2.id): 1}}
        response = await async_client.put(
            f"/api/v1/playlists/{playlist.id}/tracks/reorder",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        tracks = data["tracks"]
        
        assert tracks[0]["track_id"] == track2.id and tracks[0]["position"] == 1
        assert tracks[1]["track_id"] == track1.id and tracks[1]["position"] == 2


class TestPlaylistAccessControl:
    """Тесты контроля доступа к плейлистам"""

    async def test_access_private_playlist_owner(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Владелец может получить доступ к своему приватному плейлисту"""
        token = create_access_token(test_user.id)

        playlist = Playlist(
            user_id=test_user.id,
            name="Private",
            is_public=False
        )
        db_session.add(playlist)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/playlists/{playlist.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    async def test_access_private_playlist_other_user(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Другой пользователь не может получить доступ к чужому приватному плейлисту"""
        token = create_access_token(test_user.id)

        # Создаём другого пользователя
        from app.models.user import User
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("pass123")
        )
        db_session.add(other_user)
        await db_session.commit()

        # Создаём приватный плейлист от имени test_user
        playlist = Playlist(
            user_id=test_user.id,
            name="Private",
            is_public=False
        )
        db_session.add(playlist)
        await db_session.commit()

        # Пытаемся получить доступ от имени other_user
        other_token = create_access_token(other_user.id)
        response = await async_client.get(
            f"/api/v1/playlists/{playlist.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )

        assert response.status_code == 403

    async def test_modify_other_user_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Нельзя редактировать чужой плейлист"""
        token = create_access_token(test_user.id)

        # Создаём другого пользователя и его плейлист
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password=get_password_hash("pass123")
        )
        db_session.add(other_user)
        await db_session.commit()

        playlist = Playlist(
            user_id=other_user.id,
            name="Not Yours",
            is_public=True
        )
        db_session.add(playlist)
        await db_session.commit()

        # Пытаемся обновить чужой плейлист
        payload = {"name": "Hacked"}
        response = await async_client.patch(
            f"/api/v1/playlists/{playlist.id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    async def test_get_nonexistent_playlist(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Запрос несуществующего плейлиста"""
        token = create_access_token(test_user.id)

        response = await async_client.get(
            "/api/v1/playlists/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

