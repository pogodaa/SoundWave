// frontend/src/components/TrackCard.tsx — Карточка трека с лайком, плейлистами и поддержкой недоступных записей Jamendo
import { useState, useCallback, memo, useRef, useEffect } from 'react';
import { Play, Heart, Clock, Loader2, AlertCircle, Trash2 } from 'lucide-react';
import { Track } from '../types/track';
import { interactionsApi } from '../api/interactions';
import { playlistsApi } from '../api/playlists';
import AddToPlaylistMenu from './playlists/AddToPlaylistMenu';

interface TrackCardProps {
  track: Track;
  onPlay: (track: Track) => void;
  /** Если задан — показываем кнопку сердца и вызываем после успешного API-like/unlike (toggleLike) */
  onLike?: (trackId: number, newIsLiked: boolean) => void;
  /** Текущее состояние лайка из внешнего store */
  isLiked?: boolean;
  /** Скрыть добавление в плейлист */
  hideAddToPlaylist?: boolean;
  /** Режим страницы плейлиста — кнопка удаления из этого плейлиста */
  playlistContextId?: number;
  onRemovedFromPlaylist?: () => void;
}

const TrackCard = ({
  track,
  onPlay,
  onLike,
  isLiked: initialIsLiked = false,
  hideAddToPlaylist = false,
  playlistContextId,
  onRemovedFromPlaylist,
}: TrackCardProps) => {
  const [isLiked, setIsLiked] = useState<boolean>(initialIsLiked);
  const [isLiking, setIsLiking] = useState(false);
  const [removingFromPl, setRemovingFromPl] = useState(false);
  const hasErrorHandled = useRef(false); // Защита от бесконечного срабатывания onError у img

  // Синхронизация с серверным/store-состоянием при изменении списков
  useEffect(() => {
    setIsLiked(initialIsLiked);
  }, [initialIsLiked]);

  const unavailable = track.is_available === false;

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayClick = () => onPlay(track);

  /** Toggle лайка: оптимистичный UI и вызов onLike родителя после успешного ответа API */
  const handleLikeClick = useCallback(async () => {
    if (!onLike) return;
    setIsLiking(true);
    const previousState = isLiked;
    setIsLiked(!isLiked);
    try {
      if (isLiked) await interactionsApi.unlikeTrack(track.id);
      else await interactionsApi.likeTrack(track.id);
      onLike(track.id, !isLiked);
    } catch (error) {
      console.error('Ошибка при изменении лайка:', error);
      setIsLiked(previousState);
      alert('Не удалось изменить лайк. Проверьте подключение.');
    } finally {
      setIsLiking(false);
    }
  }, [track.id, isLiked, onLike]);

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    if (hasErrorHandled.current) return;
    hasErrorHandled.current = true;
    e.currentTarget.src = '/default-cover.jpg';
  };

  /** Удаление трека из текущего плейлиста (страница просмотра плейлиста) */
  const handleRemoveFromPlaylist = useCallback(async () => {
    if (!playlistContextId) return;
    if (
      !window.confirm(`Убрать «${track.title}» из плейлиста?`)
    ) {
      return;
    }
    setRemovingFromPl(true);
    try {
      await playlistsApi.removeTrack(playlistContextId, track.id);
      onRemovedFromPlaylist?.();
    } catch (e) {
      console.error(e);
      alert('Не удалось удалить трек из плейлиста');
    } finally {
      setRemovingFromPl(false);
    }
  }, [playlistContextId, track.id, track.title, onRemovedFromPlaylist]);

  return (
    <div
      className={`bg-gray-800 rounded-xl p-4 border transition group ${
        unavailable
          ? 'border-amber-700/50 opacity-[0.55] hover:border-amber-600/60'
          : 'border-gray-700 hover:border-gray-600'
      }`}
    >
      {/* Верх: обложка + название и исполнитель */}
      <div className="flex items-start gap-4">
        <div className="relative flex-shrink-0">
          <img
            src={track.cover_url || '/default-cover.jpg'}
            loading="lazy"
            alt={track.title}
            className="w-16 h-16 rounded-lg object-cover bg-gray-700"
            onError={handleImageError}
          />
          <button
            type="button"
            onClick={handlePlayClick}
            className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="Воспроизвести"
          >
            <Play className="w-6 h-6 text-white fill-white" />
          </button>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 min-w-0">
            <div className="min-w-0 flex-1">
              <h3
                className="text-xl font-bold text-white line-clamp-1"
                title={track.title}
              >
                {track.title}
              </h3>
              <p
                className="text-sm text-gray-400 line-clamp-1 mt-0.5"
                title={track.artist_name}
              >
                {track.artist_name}
              </p>
            </div>
            {unavailable && (
              <span className="inline-flex items-center gap-1 shrink-0 text-xs px-2 py-0.5 rounded bg-amber-900/70 text-amber-200 border border-amber-700/50">
                <AlertCircle className="w-3.5 h-3.5" />
                Недоступен
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Подвал: жанр, длительность и действия */}
      <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-gray-700/80">
        {track.genre ? (
          <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded truncate max-w-[45%]">
            {track.genre}
          </span>
        ) : (
          <span className="px-2 py-0.5 text-xs bg-gray-700/50 text-gray-500 rounded">
            Жанр не указан
          </span>
        )}

        <div className="flex items-center gap-1 shrink-0">
          <span className="text-sm text-gray-400 flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            {formatDuration(track.duration)}
          </span>
          {!hideAddToPlaylist && !playlistContextId ? (
            <AddToPlaylistMenu track={track} />
          ) : null}
          {playlistContextId ? (
            <button
              type="button"
              title="Убрать из плейлиста"
              disabled={removingFromPl}
              onClick={handleRemoveFromPlaylist}
              className="p-1.5 rounded-full text-gray-400 hover:text-red-400 hover:bg-gray-700 disabled:opacity-40 transition"
            >
              {removingFromPl ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Trash2 className="w-5 h-5" />
              )}
            </button>
          ) : null}
          {onLike && (
            <button
              type="button"
              onClick={handleLikeClick}
              disabled={isLiking}
              className={`p-1.5 rounded-full transition ${
                isLiked ? 'text-red-500 hover:text-red-400' : 'text-gray-400 hover:text-red-400'
              } ${isLiking ? 'opacity-50 cursor-wait' : ''}`}
              aria-label={isLiked ? 'Убрать из понравившихся' : 'Добавить в понравившиеся'}
            >
              {isLiking ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default memo(TrackCard);
