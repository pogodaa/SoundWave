// frontend/src/lib/playUrlCache.ts
const playUrlCache = new Map<number, string>();

export const setPlayUrl = (trackId: number, url: string) => {
  playUrlCache.set(trackId, url);
};

// Удаляет кэш прямой ссылки (перед принудительным запросом /play-url для битых треков).
export const removePlayUrl = (trackId: number) => {
  playUrlCache.delete(trackId);
};

export const getCachedPlayUrl = (trackId: number): string | undefined => {
  return playUrlCache.get(trackId);
};

export const clearPlayUrlCache = () => playUrlCache.clear();