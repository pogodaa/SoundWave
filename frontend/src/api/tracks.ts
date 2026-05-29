// frontend/src/api/tracks.ts
import api from './client';
import { Track } from '../types/track';

export interface PlayUrlResponse {
  audio_url: string;
  track_id: number;
  expires_at: string;
  refreshed: boolean;
}

/** Лимит треков в результатах поиска (согласован с бэкендом) */
export const SEARCH_TRACKS_LIMIT = 20;

export const tracksApi = {
  // Получение популярных треков
  getPopular: async (limit: number = 20): Promise<Track[]> => {
    const { data } = await api.get<Track[]>('/tracks/popular', {
      params: { limit },
    });
    return data;
  },

  // Поиск треков (явно запрашиваем до 20 результатов)
  search: async (query: string, limit: number = SEARCH_TRACKS_LIMIT): Promise<Track[]> => {
    const { data } = await api.get<Track[]>('/tracks/search', {
      params: { q: query, limit },
    });
    return data;
  },

  // Получение актуальной прямой ссылки для воспроизведения
  // Возвращает ссылку на CDN Jamendo, которую можно использовать в <audio src="...">
  getPlayUrl: async (trackId: number): Promise<PlayUrlResponse> => {
    const { data } = await api.get<PlayUrlResponse>(`/tracks/${trackId}/play-url`);
    return data;
  },
};