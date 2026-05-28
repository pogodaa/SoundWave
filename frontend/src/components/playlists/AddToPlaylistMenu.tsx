// frontend/src/components/playlists/AddToPlaylistMenu.tsx — Добавление трека в плейлист (выпадающий список)

import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ListMusic, Loader2 } from 'lucide-react';

import type { Track } from '../../types/track';
import { playlistsApi } from '../../api/playlists';
import { usePlaylistsStore } from '../../store/playlistsStore';

interface AddToPlaylistMenuProps {
  track: Track;
}

export default function AddToPlaylistMenu({ track }: AddToPlaylistMenuProps) {
  const [open, setOpen] = useState(false);
  const [addingId, setAddingId] = useState<number | null>(null);

  const playlists = usePlaylistsStore((s) => s.playlists);
  const fetchPlaylists = usePlaylistsStore((s) => s.fetchPlaylists);
  const mergePlaylist = usePlaylistsStore((s) => s.mergePlaylist);

  const rootRef = useRef<HTMLDivElement>(null);

  // При открытии подгружаем список плейлистов
  useEffect(() => {
    if (!open) return;
    void fetchPlaylists().catch(() => {});
  }, [open, fetchPlaylists]);

  // Закрытие по клику снаружи
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const handlePick = async (playlistId: number) => {
    setAddingId(playlistId);
    try {
      const updated = await playlistsApi.addTrack(playlistId, track.id);
      mergePlaylist(updated);
      setOpen(false);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string | string[] } } };
      const d = ax?.response?.data?.detail;
      const msg =
        typeof d === 'string'
          ? d
          : Array.isArray(d)
            ? d.map((x) => (typeof x === 'object' ? JSON.stringify(x) : String(x))).join(', ')
            : 'Не удалось добавить трек в плейлист';
      alert(msg);
    } finally {
      setAddingId(null);
    }
  };

  const alreadyIn = (playlistId: number) =>
    playlists.find((p) => p.id === playlistId)?.tracks.some((t) => t.track_id === track.id) ?? false;

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`p-1.5 rounded-full transition border ${
          open
            ? 'border-blue-500 text-blue-400 bg-blue-500/10'
            : 'border-transparent text-gray-400 hover:text-teal-300 hover:bg-gray-700/80'
        }`}
        title="Добавить в плейлист"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <ListMusic className="w-5 h-5" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-64 max-h-72 overflow-y-auto rounded-xl border border-gray-600 bg-gray-900 shadow-xl z-[90] py-1">
          <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-700">
            Выберите плейлист
          </div>
          {playlists.length === 0 && (
            <div className="px-3 py-4 text-sm text-gray-400">
              Нет плейлистов.{' '}
              <Link
                to="/playlists"
                className="text-blue-400 hover:underline"
                onClick={() => setOpen(false)}
              >
                Создать
              </Link>
            </div>
          )}
          {playlists.map((pl) => {
            const inPl = alreadyIn(pl.id);
            const busy = addingId === pl.id;
            return (
              <button
                key={pl.id}
                type="button"
                disabled={inPl || busy}
                onClick={() => handlePick(pl.id)}
                className="w-full text-left px-3 py-2.5 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-45 disabled:cursor-not-allowed flex items-center justify-between gap-2"
              >
                <span className="truncate">{pl.name}</span>
                {busy ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : null}
                {inPl && !busy ? (
                  <span className="text-xs text-gray-500 shrink-0">уже есть</span>
                ) : null}
              </button>
            );
          })}
          <Link
            to="/playlists"
            className="block px-3 py-2.5 text-sm text-blue-400 hover:bg-gray-800 border-t border-gray-700"
            onClick={() => setOpen(false)}
          >
            Управление плейлистами…
          </Link>
        </div>
      )}
    </div>
  );
}
