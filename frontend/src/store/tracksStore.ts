import { create } from 'zustand';

import { tracksApi } from '../api/tracks';
import { Track } from '../types/track';

interface TracksState {
  popularTracks: Track[];
  isLoaded: boolean;
  isLoading: boolean;
  error: string | null;
  fetchPopularTracks: (forceRefresh?: boolean) => Promise<void>;
  clearPopularCache: () => void;
}

export const useTracksStore = create<TracksState>((set, get) => ({
  popularTracks: [],
  isLoaded: false,
  isLoading: false,
  error: null,

  fetchPopularTracks: async (forceRefresh = false) => {
    const state = get();
    if (state.isLoading) return;
    if (state.isLoaded && !forceRefresh) return;

    set({ isLoading: true, error: null });
    try {
      const data = await tracksApi.getPopular(20);
      const availableTracks = data.filter((track) => track.is_available !== false);
      set({
        popularTracks: availableTracks,
        isLoaded: true,
        isLoading: false,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Ошибка загрузки популярных треков';
      set({ isLoading: false, error: message });
    }
  },

  clearPopularCache: () => {
    set({
      popularTracks: [],
      isLoaded: false,
      error: null,
    });
  },
}));
