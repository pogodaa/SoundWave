// frontend/src/pages/PlaylistsPage.tsx — Список плейлистов пользователя

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ListMusic, Plus, Loader2, Disc3 } from 'lucide-react';

import { usePlaylistsStore } from '../store/playlistsStore';
import type { PlaylistRead } from '../types/playlist';
import CreatePlaylistModal from '../components/playlists/CreatePlaylistModal';

function playlistCover(pl: PlaylistRead): string | null {
  const first = [...pl.tracks].sort((a, b) => a.position - b.position)[0];
  return first?.cover_url || null;
}

export default function PlaylistsPage() {
  const { playlists, loading, error, fetchPlaylists } = usePlaylistsStore();
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    void fetchPlaylists();
  }, [fetchPlaylists]);

  if (loading && playlists.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <Loader2 className="w-12 h-12 text-blue-400 animate-spin" />
        <p className="text-gray-400">Загружаем плейлисты…</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <ListMusic className="w-8 h-8 text-blue-400" />
            Мои плейлисты
          </h1>
          <p className="text-gray-400 mt-1">
            Приватные коллекции — видны только вам. Откройте плейлист, чтобы воспроизвести или изменить состав.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium transition shrink-0"
        >
          <Plus className="w-5 h-5" />
          Создать новый плейлист
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-900/30 border border-red-700/50 text-red-200 text-sm">
          {error}
        </div>
      )}

      {playlists.length === 0 ? (
        <div className="text-center py-20 px-4 rounded-2xl border border-dashed border-gray-600 bg-gray-800/40">
          <Disc3 className="w-14 h-14 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-300 mb-2">У вас пока нет плейлистов</p>
          <p className="text-gray-500 text-sm mb-6">
            Создайте первый — добавлять треки можно из страниц «Треки» и «Понравившиеся».
          </p>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white transition"
          >
            Создать плейлист
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {playlists.map((pl) => (
            <Link
              key={pl.id}
              to={`/playlists/${pl.id}`}
              className="group block bg-gray-800 rounded-2xl border border-gray-700 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10 transition overflow-hidden text-left"
            >
              <div className="aspect-[4/3] bg-gray-900 relative flex items-center justify-center overflow-hidden">
                {playlistCover(pl) ? (
                  <img
                    src={playlistCover(pl)!}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition duration-500"
                  />
                ) : (
                  <ListMusic className="w-16 h-16 text-gray-600" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                <span className="absolute bottom-3 left-3 right-3 text-white font-semibold text-lg drop-shadow line-clamp-2">
                  {pl.name}
                </span>
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-400 line-clamp-2 min-h-[2.5rem]">
                  {pl.description || 'Без описания'}
                </p>
                <p className="text-xs text-gray-500 mt-3">
                  {pl.tracks.length}{' '}
                  {pl.tracks.length === 1 ? 'трек' : pl.tracks.length < 5 ? 'трека' : 'треков'}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}

      <CreatePlaylistModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
