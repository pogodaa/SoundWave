// frontend/src/hooks/useAudioPlayer.ts — Версия с использованием playUrlCache и обработкой битых треков
import { useRef, useEffect, useCallback, useState } from 'react';
import { tracksApi } from '../api/tracks';
import { getCachedPlayUrl, setPlayUrl, removePlayUrl } from '../lib/playUrlCache';

/** Опции воспроизведения при запросе /play-url */
export interface PlayPlaybackOptions {
  /** true = трек помечен недоступным — не используем кэш URL, пробуем обновить ссылку через API */
  trackUnavailable?: boolean;
}

interface UseAudioPlayerOptions {
  onTimeUpdate?: (time: number) => void;
  onLoadedMetadata?: (duration: number) => void;
  onEnded?: () => void;
  onError?: (error: string) => void;
}

let globalAudioRef: HTMLAudioElement | null = null;
let hasInitializedGlobal = false;

export function useAudioPlayer(options: UseAudioPlayerOptions = {}) {
  const optionsRef = useRef(options);
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastTrackIdRef = useRef<number | null>(null);
  const isLoadingRef = useRef(false);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  useEffect(() => {
    if (hasInitializedGlobal) return;

    console.log('[useAudioPlayer] Глобальная инициализация Audio-элемента');
    const audio = new Audio();
    audio.preload = 'auto';
    globalAudioRef = audio;
    hasInitializedGlobal = true;

    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        console.log(`[useAudioPlayer] loadedmetadata: duration=${audio.duration.toFixed(2)}s`);
        setIsReady(true);
        setIsLoading(false);
        isLoadingRef.current = false;
        optionsRef.current.onLoadedMetadata?.(audio.duration);
      }
    };

    const handleTimeUpdate = () => optionsRef.current.onTimeUpdate?.(audio.currentTime);
    const handleEnded = () => {
      optionsRef.current.onEnded?.();
      setIsReady(false);
    };
    const handleError = () => {
      const msg = audio.error?.message || 'Ошибка загрузки аудио';
      console.error('[useAudioPlayer] error:', msg);
      setError(msg);
      setIsLoading(false);
      isLoadingRef.current = false;
      setIsReady(false);
      optionsRef.current.onError?.(msg);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('loadstart', () => {
      setIsLoading(true);
      isLoadingRef.current = true;
    });

    return () => {};
  }, []);

  const play = useCallback(async (trackId: number, playback?: PlayPlaybackOptions): Promise<boolean> => {
    if (lastTrackIdRef.current === trackId && isLoadingRef.current) {
      console.log(`[useAudioPlayer] Игнорируем повторный play для трека ${trackId}`);
      return true;
    }

    lastTrackIdRef.current = trackId;
    if (!globalAudioRef) return false;

    const audio = globalAudioRef;
    const forceRefresh = playback?.trackUnavailable === true;

    try {
      setError(null);
      setIsLoading(true);
      isLoadingRef.current = true;

      if (forceRefresh) {
        removePlayUrl(trackId);
      }

      let audio_url = forceRefresh ? undefined : getCachedPlayUrl(trackId);

      if (!audio_url) {
        console.log(
          forceRefresh
            ? `[useAudioPlayer] Трек ${trackId} недоступен в кэше — запрашиваем /play-url`
            : `[useAudioPlayer] Кэш miss для трека ${trackId}, запрашиваем...`
        );
        try {
          const response = await tracksApi.getPlayUrl(trackId);
          audio_url = response.audio_url;
          setPlayUrl(trackId, audio_url);
        } catch (err: unknown) {
          const ax = err as { response?: { status?: number } };
          const status = ax?.response?.status;
          if (status === 404 || status === 502) {
            const msg = 'Трек больше недоступен на Jamendo';
            setError(msg);
            setIsLoading(false);
            isLoadingRef.current = false;
            setIsReady(false);
            optionsRef.current.onError?.(msg);
            return false;
          }
          throw err;
        }
      } else {
        console.log(`[useAudioPlayer] Используем кэшированную audio_url для трека ${trackId}`);
      }

      if (audio.src !== audio_url) {
        setIsReady(false);
        audio.pause();
        audio.src = audio_url;
        audio.load();
      }

      await audio.play().catch((err) => {
        if (err.name !== 'AbortError') console.error('play() error:', err);
      });

      setIsLoading(false);
      isLoadingRef.current = false;
      return true;
    } catch (err: unknown) {
      const e = err as { name?: string; message?: string };
      if (e.name === 'AbortError') return false;
      setError(e.message || 'Ошибка воспроизведения');
      setIsLoading(false);
      isLoadingRef.current = false;
      setIsReady(false);
      return false;
    }
  }, []);

  const pause = useCallback(() => {
    globalAudioRef?.pause();
  }, []);

  const togglePlay = useCallback(
    async (trackId: number, isPlaying: boolean, playback?: PlayPlaybackOptions): Promise<boolean> => {
      // isPlaying = текущее состояние «играет» из playerStore: true → пауза, false → play
      if (isPlaying) {
        pause();
        return true;
      }
      return await play(trackId, playback);
    },
    [play, pause]
  );

  const seek = useCallback((time: number) => {
    if (globalAudioRef && !isNaN(time) && isFinite(time)) {
      globalAudioRef.currentTime = time;
    }
  }, []);

  const setVolume = useCallback((volume: number) => {
    if (globalAudioRef) {
      globalAudioRef.volume = Math.max(0, Math.min(1, volume));
    }
  }, []);

  return {
    isReady,
    isLoading,
    error,
    play,
    pause,
    togglePlay,
    seek,
    setVolume,
    clearError: () => setError(null),
  };
}
