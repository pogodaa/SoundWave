// frontend/src/store/playlistsStore.ts — Кэш плейлистов пользователя (Zustand)

import { create } from 'zustand';

import { playlistsApi } from '../api/playlists';
import type { PlaylistRead } from '../types/playlist';

interface PlaylistsState {
  playlists: PlaylistRead[];
  loading: boolean;
  error: string | null;
  /** Загрузка списка с сервера */
  fetchPlaylists: () => Promise<void>;
  /** Обновить или добавить плейлист после мутаций (ответ API уже полный) */
  mergePlaylist: (playlist: PlaylistRead) => void;
  /** Создать плейлист и добавить в кэш */
  createPlaylist: (name: string, description?: string | null) => Promise<PlaylistRead>;
}

export const usePlaylistsStore = create<PlaylistsState>((set, get) => ({
  playlists: [],
  loading: false,
  error: null,

  fetchPlaylists: async () => {
    set({ loading: true, error: null });
    try {
      const data = await playlistsApi.list();
      set({ playlists: data, loading: false });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Не удалось загрузить плейлисты';
      set({ loading: false, error: msg });
    }
  },

  mergePlaylist: (playlist: PlaylistRead) =>
    set((state) => {
      const ix = state.playlists.findIndex((p) => p.id === playlist.id);
      if (ix < 0) {
        return { playlists: [...state.playlists, playlist] };
      }
      const copy = [...state.playlists];
      copy[ix] = playlist;
      return { playlists: copy };
    }),

  createPlaylist: async (name: string, description?: string | null) => {
    const created = await playlistsApi.create({ name, description });
    get().mergePlaylist(created);
    return created;
  },
}));
