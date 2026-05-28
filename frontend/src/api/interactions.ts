// frontend/src/api/interactions.ts — API-клиент для лайков и сводки рекомендаций
import client from './client';
import type { Track } from '../types/track';

export interface LikeResponse {
  message: string;
}

/** Элемент списка /interactions/likes с полными данными трека */
export interface LikedTrackItem {
  liked_at: string;
  track: Track;
}

export interface InteractionsSummary {
  total_likes: number;
  /** Всегда 0: история прослушиваний на бэкенде отключена */
  total_listens: number;
  favorite_genres: string[];
}

export const interactionsApi = {
  /** Добавить лайк к треку */
  async likeTrack(trackId: number): Promise<LikeResponse> {
    const response = await client.post<LikeResponse>(`/interactions/like/${trackId}`);
    return response.data;
  },

  /** Удалить лайк с трека */
  async unlikeTrack(trackId: number): Promise<LikeResponse> {
    const response = await client.delete<LikeResponse>(`/interactions/like/${trackId}`);
    return response.data;
  },

  /** Список лайков с полными данными треков */
  async getLikedTracks(limit: number = 200): Promise<LikedTrackItem[]> {
    const response = await client.get<LikedTrackItem[]>(`/interactions/likes?limit=${limit}`);
    return response.data;
  },

  /** Сводка по взаимодействиям (рекомендации строятся по лайкам) */
  async getSummary(): Promise<InteractionsSummary> {
    const response = await client.get<InteractionsSummary>('/interactions/summary');
    return response.data;
  },

  /** Проверить, лайкнут ли трек (через список лайков) */
  async isTrackLiked(trackId: number): Promise<boolean> {
    try {
      const liked = await this.getLikedTracks(200);
      return liked.some((item) => item.track.id === trackId);
    } catch {
      return false;
    }
  },
};
