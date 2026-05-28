// frontend/src/pages/PlaylistDetailPage.tsx — Просмотр одного плейлиста и воспроизведение очереди

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ListMusic, Loader2, Play } from 'lucide-react';

import TrackCard from '../components/TrackCard';
import { usePlayer } from '../store/playerStore';
import { useLikedTracksStore } from '../store/likedTracksStore';
import { usePlaylistsStore } from '../store/playlistsStore';
import { playlistsApi } from '../api/playlists';
import type { PlaylistRead } from '../types/playlist';
import type { Track } from '../types/track';
import { playlistTrackReadToTrack } from '../utils/playlistTrackMap';

export default function PlaylistDetailPage() {
  const { playlistId: idParam } = useParams<{ playlistId: string }>();
  const playlistId = Number(idParam);

  const [playlist, setPlaylist] = useState<PlaylistRead | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const playTrack = usePlayer((s) => s.playTrack);
  const mergePlaylist = usePlaylistsStore((s) => s.mergePlaylist);

  const likedIds = useLikedTracksStore((s) => s.likedIds);
  const setLikeState = useLikedTracksStore((s) => s.setLikeState);

  const currentListRef = useRef<Track[]>([]);

  const reload = useCallback(async () => {
    if (!Number.isFinite(playlistId) || playlistId < 1) {
      setLoadError('Некорректный плейлист');
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError(null);
    try {
      const data = await playlistsApi.getById(playlistId);
      setPlaylist(data);
      mergePlaylist(data);
    } catch {
      setLoadError('Плейлист не найден или нет доступа');
      setPlaylist(null);
    } finally {
      setLoading(false);
    }
  }, [playlistId, mergePlaylist]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const sortedTracks = useMemo(() => {
    if (!playlist) return [];
    return [...playlist.tracks].sort((a, b) => a.position - b.position);
  }, [playlist]);

  const queue: Track[] = useMemo(
    () => sortedTracks.map((pt) => playlistTrackReadToTrack(pt)),
    [sortedTracks]
  );

  useEffect(() => {
    currentListRef.current = queue;
  }, [queue]);

  const handlePlay = useCallback(
    (track: Track) => {
      playTrack(track, currentListRef.current);
    },
    [playTrack]
  );

  const handlePlayAll = useCallback(() => {
    if (!queue.length) return;
    playTrack(queue[0], queue);
  }, [queue, playTrack]);

  if (!Number.isFinite(playlistId) || playlistId < 1) {
    return (
      <div className="p-6 text-center text-red-300">
        Некорректная ссылка. <Link to="/playlists" className="text-blue-400 underline">К списку</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[45vh] gap-3">
        <Loader2 className="w-11 h-11 text-blue-400 animate-spin" />
        <p className="text-gray-400">Загружаем плейлист…</p>
      </div>
    );
  }

  if (loadError || !playlist) {
    return (
      <div className="p-6 max-w-lg mx-auto text-center">
        <p className="text-red-300 mb-4">{loadError}</p>
        <Link to="/playlists" className="text-blue-400 hover:underline">
          ← Все плейлисты
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <Link
        to="/playlists"
        className="inline-flex items-center gap-2 text-gray-400 hover:text-white text-sm mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Все плейлисты
      </Link>

      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-8">
        <div className="flex gap-5 min-w-0">
          <div className="w-28 h-28 sm:w-36 sm:h-36 rounded-2xl bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0 overflow-hidden">
            {queue[0]?.cover_url ? (
              <img src={queue[0].cover_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <ListMusic className="w-14 h-14 text-gray-600" />
            )}
          </div>
          <div className="min-w-0">
            <h1 className="text-3xl font-bold text-white truncate">{playlist.name}</h1>
            <p className="text-gray-400 mt-2 line-clamp-3">
              {playlist.description || 'Без описания'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {queue.length}{' '}
              {queue.length === 1 ? 'трек' : queue.length < 5 ? 'трека' : 'треков'} · только вы
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handlePlayAll}
          disabled={queue.length === 0}
          className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold shrink-0 transition"
        >
          <Play className="w-5 h-5 fill-current" />
          Воспроизвести весь плейлист
        </button>
      </div>

      {queue.length === 0 ? (
        <p className="text-gray-500 text-center py-16 border border-dashed border-gray-700 rounded-2xl">
          В плейлисте пока нет треков. Добавляйте их из каталога или «Понравившиеся».
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {queue.map((track) => (
            <TrackCard
              key={track.id}
              track={track}
              onPlay={handlePlay}
              isLiked={likedIds.has(track.id)}
              onLike={(tid, liked) => setLikeState(tid, liked)}
              playlistContextId={playlist.id}
              onRemovedFromPlaylist={reload}
              hideAddToPlaylist
            />
          ))}
        </div>
      )}
    </div>
  );
}
