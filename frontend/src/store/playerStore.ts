// frontend/src/store/playerStore.ts — Стабильная версия с защитой от повторного play
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Track } from '../types/track';

interface PlayerState {
  currentTrack: Track | null;
  queue: Track[];
  queueIndex: number;
  isPlaying: boolean;
  progress: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isLoading: boolean;
  error: string | null;

  playTrack: (track: Track, newQueue?: Track[]) => Promise<void>;
  togglePlay: () => Promise<void>;
  nextTrack: () => Promise<void>;
  prevTrack: () => Promise<void>;
  seekTo: (time: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  onTimeUpdate: (time: number) => void;
  onLoadedMetadata: (duration: number) => void;
  onEnded: () => void;
  onError: (message: string) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
}

const safeStorage = {
  getItem: (name: string) => {
    try {
      const item = localStorage.getItem(name);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  setItem: (name: string, value: any) => localStorage.setItem(name, JSON.stringify(value)),
  removeItem: (name: string) => localStorage.removeItem(name),
};

export const usePlayer = create<PlayerState>()(
  persist(
    (set, get) => ({
      currentTrack: null,
      queue: [],
      queueIndex: -1,
      isPlaying: false,
      progress: 0,
      duration: 0,
      volume: 1.0,
      isMuted: false,
      isLoading: false,
      error: null,

      playTrack: async (track, newQueue) => {
        const state = get();

        if (state.currentTrack?.id === track.id && state.isPlaying) {
          console.log(`[playerStore] Трек ${track.id} уже играет — игнорируем повторный playTrack`);
          return;
        }

        const audioElement = document.querySelector('audio');
        if (audioElement) audioElement.pause();

        if (newQueue?.length) {
          const index = newQueue.findIndex((t) => t.id === track.id);
          set({ queue: newQueue, queueIndex: index >= 0 ? index : 0 });
        } else if (!state.queue.some((t) => t.id === track.id)) {
          set({ queue: [track], queueIndex: 0 });
        } else {
          const index = state.queue.findIndex((t) => t.id === track.id);
          set({ queueIndex: index });
        }

        set({
          currentTrack: track,
          isPlaying: true,
          progress: 0,
          error: null,
        });
      },

      togglePlay: async () => {
        const { isPlaying } = get();
        set({ isPlaying: !isPlaying });
      },

      nextTrack: async () => {
        const { queue, queueIndex } = get();
        if (!queue.length) return;
        const nextIndex = queueIndex + 1;
        if (nextIndex < queue.length) {
          await get().playTrack(queue[nextIndex]);
        } else {
          set({ isPlaying: false });
        }
      },

      prevTrack: async () => {
        const { queue, queueIndex } = get();
        if (!queue.length) return;
        const prevIndex = Math.max(0, queueIndex - 1);
        await get().playTrack(queue[prevIndex]);
      },

      seekTo: (time) => set({ progress: time }),
      setVolume: (volume) => {
        const clamped = Math.max(0, Math.min(1, volume));
        set({ volume: clamped, isMuted: clamped === 0 });
      },
      toggleMute: () => {
        const { isMuted, volume, setVolume } = get();
        setVolume(isMuted ? (volume > 0 ? volume : 0.5) : 0);
        set({ isMuted: !isMuted });
      },

      onTimeUpdate: (time) => set({ progress: time }),
      onLoadedMetadata: (duration) => set({ duration, isLoading: false }),
      onEnded: () => {
        get().nextTrack();
      },
      onError: (message) => set({ error: message, isLoading: false, isPlaying: false }),
      setLoading: (loading) => set({ isLoading: loading }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'soundwave-player',
      storage: createJSONStorage(() => safeStorage),
      partialize: (state) => ({
        volume: state.volume,
        isMuted: state.isMuted,
        currentTrackId: state.currentTrack?.id ?? null,
      }),
    }
  )
);
