// frontend/src/components/player/Player.tsx — Добавлен onSlowTrack
import { useEffect, useCallback } from 'react';
import {
    Play,
    Pause,
    SkipForward,
    SkipBack,
    Volume2,
    VolumeX,
    Volume1,
    Loader2,
    AlertCircle,
} from 'lucide-react';
import { usePlayer } from '../../store/playerStore';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';

export default function Player() {
    const {
        currentTrack,
        isPlaying,
        progress,
        duration,
        volume,
        isMuted,
        isLoading,
        error,
        togglePlay,
        nextTrack,
        prevTrack,
        seekTo,
        setVolume,
        onTimeUpdate,
        onLoadedMetadata,
        onEnded,
        onError,
        clearError,
    } = usePlayer();

    const {
        isReady,
        isLoading: audioIsLoading,
        error: audioError,
        togglePlay: toggleAudioPlay,
        seek,
        setVolume: setAudioVolume,
        clearError: clearAudioError,
    } = useAudioPlayer({
        onTimeUpdate,
        onLoadedMetadata,
        onEnded,
        onError: (msg) => onError(msg),
    });

    // Синхронизация громкости между стейтом и аудио-элементом
    useEffect(() => {
        setAudioVolume(isMuted ? 0 : volume);
    }, [volume, isMuted, setAudioVolume]);

    // Автоматическое воспроизведение при смене трека
    useEffect(() => {
        if (!currentTrack) return;

        const attemptPlay = async () => {
            try {
                if (isPlaying) {
                    await toggleAudioPlay(currentTrack.id, false, {
                        trackUnavailable: currentTrack.is_available === false,
                    });
                } else {
                    await toggleAudioPlay(currentTrack.id, true);
                }
            } catch (err) {
                console.error('Ошибка воспроизведения:', err);
            }
        };

        attemptPlay();
    }, [currentTrack?.id, currentTrack?.is_available, isPlaying, toggleAudioPlay]);

    // Обработчик переключения play/pause по клику пользователя
    const handleTogglePlay = useCallback(async () => {
        if (!currentTrack) return;

        clearError();
        clearAudioError();

        try {
            await toggleAudioPlay(
                currentTrack.id,
                isPlaying,
                !isPlaying && currentTrack.is_available === false
                    ? { trackUnavailable: true }
                    : undefined
            );
            await togglePlay();
        } catch (err) {
            console.error('Ошибка переключения воспроизведения:', err);
        }
    }, [currentTrack, isPlaying, toggleAudioPlay, togglePlay, clearError, clearAudioError]);

    // Обработчик перемотки
    const handleSeek = useCallback((value: number) => {
        seekTo(value);
        seek(value);
    }, [seekTo, seek]);

    // Форматирование времени в мм:сс
    const formatTime = (seconds: number): string => {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Если нет текущего трека — не рендерим плеер
    if (!currentTrack) return null;

    // Выбор иконки громкости в зависимости от уровня
    const VolumeIcon = isMuted || volume === 0 ? VolumeX : volume < 0.5 ? Volume1 : Volume2;
    const displayError = error || audioError;
    const displayLoading = isLoading || audioIsLoading;

    return (
        <>
            <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 px-4 py-3 z-50">
                <div className="max-w-7xl mx-auto flex items-center gap-4">
                    {/* Информация о треке */}
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                        <img
                            src={currentTrack.cover_url || '/default-cover.png'}
                            alt={currentTrack.title}
                            className="w-14 h-14 rounded-lg object-cover bg-gray-700 flex-shrink-0"
                            onError={(e) => {
                                (e.target as HTMLImageElement).src = '/default-cover.png';
                            }}
                        />
                        <div className="min-w-0">
                            <p className="font-medium text-white truncate text-sm" title={currentTrack.title}>
                                {currentTrack.title}
                            </p>
                            <p className="text-xs text-gray-400 truncate" title={currentTrack.artist_name}>
                                {currentTrack.artist_name}
                            </p>
                        </div>
                    </div>

                    {/* Кнопки управления */}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={prevTrack}
                            className="text-gray-400 hover:text-white transition p-1 disabled:opacity-50"
                            aria-label="Предыдущий трек"
                            disabled={displayLoading}
                        >
                            <SkipBack className="w-5 h-5" />
                        </button>

                        <button
                            onClick={handleTogglePlay}
                            className="w-10 h-10 flex items-center justify-center bg-blue-600 hover:bg-blue-700 rounded-full transition disabled:opacity-50"
                            aria-label={isPlaying ? 'Пауза' : 'Воспроизвести'}
                            disabled={displayLoading || !!displayError}
                        >
                            {displayLoading ? (
                                <Loader2 className="w-5 h-5 text-white animate-spin" />
                            ) : isPlaying ? (
                                <Pause className="w-5 h-5 text-white" />
                            ) : (
                                <Play className="w-5 h-5 text-white fill-white" />
                            )}
                        </button>

                        <button
                            onClick={nextTrack}
                            className="text-gray-400 hover:text-white transition p-1 disabled:opacity-50"
                            aria-label="Следующий трек"
                            disabled={displayLoading}
                        >
                            <SkipForward className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Прогресс и громкость */}
                    <div className="flex items-center gap-4 flex-1 justify-end">
                        <div className="hidden sm:flex items-center gap-2 w-48">
                            <span className="text-xs text-gray-400 w-10 text-right">
                                {formatTime(progress)}
                            </span>
                            <input
                                type="range"
                                min={0}
                                max={duration || 100}
                                value={progress}
                                onChange={(e) => handleSeek(Number(e.target.value))}
                                disabled={!isReady || displayLoading}
                                className="flex-1 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500 disabled:opacity-50"
                            />
                            <span className="text-xs text-gray-400 w-10">
                                {formatTime(duration)}
                            </span>
                        </div>

                        <div className="hidden md:flex items-center gap-2 w-32">
                            <button
                                onClick={() => setVolume(isMuted ? (volume > 0 ? volume : 0.5) : 0)}
                                className="text-gray-400 hover:text-white transition"
                                aria-label={isMuted ? 'Включить звук' : 'Выключить звук'}
                            >
                                <VolumeIcon className="w-5 h-5" />
                            </button>
                            <input
                                type="range"
                                min={0}
                                max={1}
                                step={0.01}
                                value={isMuted ? 0 : volume}
                                onChange={(e) => setVolume(Number(e.target.value))}
                                className="flex-1 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Отображение ошибки, если есть */}
                {displayError && (
                    <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span>{displayError}</span>
                        <button onClick={clearError} className="ml-2 text-red-300 hover:text-red-200">
                            Закрыть
                        </button>
                    </div>
                )}
            </div>
            {/* Отступ чтобы контент не перекрывался плеером */}
            <div className="h-24" />
        </>
    );
}