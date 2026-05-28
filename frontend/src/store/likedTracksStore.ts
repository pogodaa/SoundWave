import { create } from 'zustand';

import { interactionsApi, LikedTrackItem } from '../api/interactions';

/** Параметры загрузки списка лайков */
export interface FetchLikedOptions {
  /** Принудительный запрос к API (для страницы «Понравившиеся») */
  force?: boolean;
}

interface LikedTracksState {
  /** ID лайкнутых треков — для иконок на странице «Треки» */
  likedIds: Set<number>;
  /** Полные элементы лайков (как с бэкенда) */
  likedItems: LikedTrackItem[];
  /** Уже подгружали лайки без force (чтобы не дёргать API при каждом заходе на «Треки») */
  isHydrated: boolean;
  loading: boolean;
  error: string | null;
  fetchLikedTracks: (options?: FetchLikedOptions) => Promise<void>;
  /** После успешного like/unlike из TrackCard — держим store в актуальном виде */
  setLikeState: (trackId: number, liked: boolean) => void;
}

export const useLikedTracksStore = create<LikedTracksState>((set, get) => ({
  likedIds: new Set(),
  likedItems: [],
  isHydrated: false,
  loading: false,
  error: null,

  fetchLikedTracks: async (options?: FetchLikedOptions) => {
    const force = options?.force === true;
    if (!force && get().isHydrated) return;

    set({ loading: true, error: null });
    try {
      const data = await interactionsApi.getLikedTracks(200);
      set({
        likedItems: data,
        likedIds: new Set(data.map((item) => item.track.id)),
        isHydrated: true,
        loading: false,
      });
    } catch (e) {
      const message =
        e instanceof Error ? e.message : 'Не удалось загрузить понравившиеся треки';
      set({ loading: false, error: message });
    }
  },

  setLikeState: (trackId, liked) =>
    set((state) => {
      const nextIds = new Set(state.likedIds);
      if (liked) nextIds.add(trackId);
      else nextIds.delete(trackId);

      let nextItems = state.likedItems;
      if (!liked && nextItems.length > 0) {
        nextItems = nextItems.filter((item) => item.track.id !== trackId);
      }

      return { likedIds: nextIds, likedItems: nextItems };
    }),
}));
