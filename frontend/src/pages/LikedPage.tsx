// frontend/src/pages/LikedPage.tsx — Лайкнутые треки (включая недоступные на Jamendo)
import { useEffect, useCallback, useRef, useMemo } from 'react';
import { Heart, Loader2 } from 'lucide-react';

import TrackCard from '../components/TrackCard';
import { usePlayer } from '../store/playerStore';
import { useLikedTracksStore } from '../store/likedTracksStore';
import { Track } from '../types/track';

export default function LikedPage() {
  const playTrack = usePlayer((s) => s.playTrack);

  const likedItems = useLikedTracksStore((s) => s.likedItems);
  const loading = useLikedTracksStore((s) => s.loading);
  const fetchLikedTracks = useLikedTracksStore((s) => s.fetchLikedTracks);
  const setLikeState = useLikedTracksStore((s) => s.setLikeState);

  const currentListRef = useRef<Track[]>([]);

  // Принудительно обновляем список при каждом заходе на страницу
  useEffect(() => {
    void fetchLikedTracks({ force: true });
  }, [fetchLikedTracks]);

  const tracks: Track[] = useMemo(
    () =>
      likedItems.map((item) => ({
        ...item.track,
        is_liked: true,
      })),
    [likedItems]
  );

  useEffect(() => {
    currentListRef.current = tracks;
  }, [tracks]);

  const handlePlay = useCallback(
    (track: Track) => {
      playTrack(track, currentListRef.current);
    },
    [playTrack]
  );

  const handleLike = useCallback((trackId: number, liked: boolean) => {
    setLikeState(trackId, liked);
  }, [setLikeState]);

  if (loading && tracks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
        <Loader2 className="w-12 h-12 text-pink-500 animate-spin mb-4" />
        <p className="text-gray-400">Загружаем понравившиеся треки…</p>
      </div>
    );
  }

  if (!loading && tracks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[55vh] text-center px-4">
        <Heart className="w-16 h-16 text-gray-600 mb-4" strokeWidth={1.25} />
        <h1 className="text-2xl font-bold text-white mb-2">Понравившиеся треки</h1>
        <p className="text-gray-400 max-w-md">
          Здесь появятся треки, которые вы отметите сердечком. Недоступные на Jamendo треки тоже можно
          увидеть в этом списке.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-2">
          <Heart className="w-8 h-8 text-red-500 fill-red-500" />
          Понравившиеся треки
        </h1>
        <p className="text-gray-400 mt-2">
          Показываются все лайки, включая треки, помеченные как недоступные при обновлении ссылок Jamendo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {tracks.map((track) => (
          <TrackCard
            key={track.id}
            track={track}
            onPlay={handlePlay}
            isLiked
            onLike={handleLike}
          />
        ))}
      </div>
    </div>
  );
}
