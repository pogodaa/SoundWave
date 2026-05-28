// frontend/src/api/playlists.ts — Клиент API плейлистов (приватные, только владелец)

import api from './client';
import type { PlaylistCreatePayload, PlaylistRead } from '../types/playlist';

export const playlistsApi = {
  /** Список плейлистов текущего пользователя (с треками) */
  async list(): Promise<PlaylistRead[]> {
    const { data } = await api.get<PlaylistRead[]>('/playlists');
    return data;
  },

  async getById(playlistId: number): Promise<PlaylistRead> {
    const { data } = await api.get<PlaylistRead>(`/playlists/${playlistId}`);
    return data;
  },

  /** Создание личного плейлиста (is_public: false) */
  async create(payload: PlaylistCreatePayload): Promise<PlaylistRead> {
    const { data } = await api.post<PlaylistRead>('/playlists', {
      name: payload.name,
      description: payload.description ?? null,
      is_public: false,
    });
    return data;
  },

  async addTrack(playlistId: number, trackId: number, position?: number): Promise<PlaylistRead> {
    const { data } = await api.post<PlaylistRead>(`/playlists/${playlistId}/tracks`, {
      track_id: trackId,
      ...(position !== undefined ? { position } : {}),
    });
    return data;
  },

  async removeTrack(playlistId: number, trackId: number): Promise<void> {
    await api.delete(`/playlists/${playlistId}/tracks/${trackId}`);
  },
};
