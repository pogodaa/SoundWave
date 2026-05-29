// frontend/src/pages/RecommendationsPage.tsx — Персональные ML-рекомендации по лайкам
import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';

import TrackCard from '../components/TrackCard';
import { recommendationsApi } from '../api/recommendations';
import { usePlayer } from '../store/playerStore';
import { useLikedTracksStore } from '../store/likedTracksStore';
import { Track } from '../types/track';

export default function RecommendationsPage() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [coldStart, setColdStart] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const playTrack = usePlayer((s) => s.playTrack);
  const likedIds = useLikedTracksStore((s) => s.likedIds);
  const fetchLikedTracks = useLikedTracksStore((s) => s.fetchLikedTracks);
  const setLikeState = useLikedTracksStore((s) => s.setLikeState);

  const currentListRef = useRef<Track[]>([]);

  useEffect(() => {
    void fetchLikedTracks();
  }, [fetchLikedTracks]);

  useEffect(() => {
    currentListRef.current = tracks;
  }, [tracks]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await recommendationsApi.getPersonal(20);
        if (cancelled) return;
        setTracks(response.tracks.filter((t) => t.is_available !== false));
        setColdStart(response.cold_start);
      } catch (err) {
        console.error('Ошибка загрузки рекомендаций:', err);
        if (!cancelled) {
          setError('Не удалось загрузить рекомендации. Попробуйте позже.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handlePlay = useCallback(
    (track: Track) => {
      playTrack(track, currentListRef.current);
    },
    [playTrack],
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
        <Loader2 className="w-12 h-12 text-purple-400 animate-spin mb-4" />
        <p className="text-gray-400">Подбираем рекомендации…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (coldStart || tracks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[55vh] text-center px-4">
        <Sparkles className="w-16 h-16 text-purple-500 mb-4" strokeWidth={1.25} />
        <h1 className="text-2xl font-bold text-white mb-2">Рекомендации для вас</h1>
        <p className="text-gray-400 max-w-md">
          Лайкайте треки, чтобы получать рекомендации. Мы анализируем жанры и теги ваших
          любимых композиций и подбираем похожую музыку.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-purple-400" />
          Рекомендации для вас
        </h1>
        <p className="text-gray-400 mt-2">
          Подборка на основе ваших лайков: Content-Based Filtering (жанры и теги).
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {tracks.map((track) => (
          <TrackCard
            key={track.id}
            track={track}
            onPlay={handlePlay}
            isLiked={likedIds.has(track.id)}
            onLike={(id, liked) => setLikeState(id, liked)}
          />
        ))}
      </div>
    </div>
  );
}
