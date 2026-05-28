// frontend/src/pages/TracksPage.tsx — Финальная стабильная версия
import { useEffect, useState, useCallback, useRef } from 'react';
import { Search, RefreshCw, Loader2 } from 'lucide-react';
import { tracksApi } from '../api/tracks';
import { Track } from '../types/track';
import TrackCard from '../components/TrackCard';
import { usePlayer } from '../store/playerStore';
import { useTracksStore } from '../store/tracksStore';
import { useLikedTracksStore } from '../store/likedTracksStore';

export default function TracksPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchResults, setSearchResults] = useState<Track[] | null>(null);

  const playTrack = usePlayer((state) => state.playTrack);
  const tracks = useTracksStore((state) => state.popularTracks);
  const isLoaded = useTracksStore((state) => state.isLoaded);
  const isLoading = useTracksStore((state) => state.isLoading);
  const fetchPopularTracks = useTracksStore((state) => state.fetchPopularTracks);
  const clearPopularCache = useTracksStore((state) => state.clearPopularCache);

  const likedIds = useLikedTracksStore((s) => s.likedIds);
  const fetchLikedTracks = useLikedTracksStore((s) => s.fetchLikedTracks);
  const setLikeState = useLikedTracksStore((s) => s.setLikeState);

  const currentListRef = useRef<Track[]>([]);

  // Один раз загружаем ID лайков для отображения сердечек на «Треках»
  useEffect(() => {
    void fetchLikedTracks();
  }, [fetchLikedTracks]);

  useEffect(() => {
    if (!isLoaded) {
      fetchPopularTracks(false);
    }
  }, [isLoaded, fetchPopularTracks]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const results = await tracksApi.search(query);
      setSearchResults(results.filter((track) => track.is_available !== false));
    } catch (error) {
      console.error('Ошибка поиска:', error);
    }
  };

  const displayTracks = searchResults ?? tracks;
  useEffect(() => {
    currentListRef.current = displayTracks;
  }, [displayTracks]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    clearPopularCache();
    setSearchResults(null);
    setSearchQuery('');
    await fetchPopularTracks(true);
    setIsRefreshing(false);
  }, [clearPopularCache, fetchPopularTracks]);

  const handlePlay = useCallback((track: Track) => {
    playTrack(track, currentListRef.current);
  }, [playTrack]);

  if (isLoading && !isLoaded) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4">
        <Loader2 className="w-14 h-14 text-blue-400 animate-spin mb-6" />
        <h2 className="text-3xl font-bold text-white mb-3">Загружаем треки...</h2>
        <p className="max-w-md text-gray-400 text-lg leading-relaxed">
          Первая загрузка списка популярных треков.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Каталог треков</h1>
          <p className="text-gray-400 mt-1">Рандомные треки</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing || isLoading}
          className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm font-medium transition"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
          Обновить
        </button>
      </div>

      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Поиск треков или исполнителей..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 focus:border-blue-500 rounded-2xl pl-11 py-4 text-white placeholder-gray-400 outline-none transition"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {displayTracks.map((track) => (
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