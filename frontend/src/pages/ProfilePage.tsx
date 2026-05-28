// frontend/src/pages/ProfilePage.tsx — Профиль пользователя

import { useNavigate } from 'react-router-dom';
import {
  User,
  Heart,
  ListMusic,
  LogOut,
  ChevronRight,
  Mail,
  Shield,
} from 'lucide-react';

import { useAuth } from '../store/auth';
import { useLikedTracksStore } from '../store/likedTracksStore';
import { usePlaylistsStore } from '../store/playlistsStore';

/** Человекочитаемая подпись роли из API */
function roleLabel(role: string): string {
  const map: Record<string, string> = {
    unverified: 'Не подтверждён',
    user: 'Пользователь',
    admin: 'Администратор',
  };
  return map[role] ?? role;
}

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const likedCount = useLikedTracksStore((s) => s.likedIds.size);
  const playlistsCount = usePlaylistsStore((s) => s.playlists.length);

  const handleLogout = () => {
    const confirmed = window.confirm(
      'Выйти из аккаунта? Текущая сессия будет завершена.'
    );
    if (confirmed) {
      logout();
    }
  };

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] text-gray-400">
        <User className="w-12 h-12 mb-3 opacity-50" />
        <p>Загрузка данных профиля…</p>
      </div>
    );
  }

  const avatarUrl = '/avatars/default1.png';

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-white">Профиль</h1>

      {/* Карточка пользователя */}
      <section className="bg-gray-800 border border-gray-700 rounded-2xl overflow-hidden">
        <div className="h-24 bg-gradient-to-r from-blue-600/40 via-indigo-600/30 to-purple-600/20" />
        <div className="px-6 pb-6 -mt-12">
          <div className="flex flex-col sm:flex-row sm:items-end gap-4">
            <div className="relative w-24 h-24 rounded-2xl border-4 border-gray-800 bg-gray-700 overflow-hidden shrink-0 shadow-lg flex items-center justify-center">
              <img
                src={avatarUrl}
                alt=""
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <User className="w-12 h-12 text-gray-400" />
            </div>
            <div className="min-w-0 pt-2 sm:pt-0 sm:pb-1">
              <h2 className="text-2xl font-bold text-white truncate">{user.username}</h2>
              <p className="text-gray-400 text-sm mt-1 flex items-center gap-1.5 truncate">
                <Mail className="w-4 h-4 shrink-0" />
                {user.email}
              </p>
              <span className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded-lg bg-gray-700/80 text-gray-300 text-xs">
                <Shield className="w-3.5 h-3.5" />
                {roleLabel(user.role)}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Статистика */}
      <section className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-red-500/15">
              <Heart className="w-5 h-5 text-red-400 fill-red-400/30" />
            </div>
            <span className="text-sm text-gray-400">Лайки</span>
          </div>
          <p className="text-3xl font-bold text-white">{likedCount}</p>
          <p className="text-xs text-gray-500 mt-1">понравившихся треков</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-blue-500/15">
              <ListMusic className="w-5 h-5 text-blue-400" />
            </div>
            <span className="text-sm text-gray-400">Плейлисты</span>
          </div>
          <p className="text-3xl font-bold text-white">{playlistsCount}</p>
          <p className="text-xs text-gray-500 mt-1">созданных коллекций</p>
        </div>
      </section>

      {/* Быстрые ссылки */}
      <section className="bg-gray-800 border border-gray-700 rounded-2xl divide-y divide-gray-700">
        <p className="px-5 pt-4 pb-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
          Быстрые ссылки
        </p>
        <button
          type="button"
          onClick={() => navigate('/playlists')}
          className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-700/50 transition"
        >
          <span className="flex items-center gap-3 text-white">
            <ListMusic className="w-5 h-5 text-blue-400" />
            Мои плейлисты
          </span>
          <ChevronRight className="w-5 h-5 text-gray-500" />
        </button>
        <button
          type="button"
          onClick={() => navigate('/liked')}
          className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-700/50 transition"
        >
          <span className="flex items-center gap-3 text-white">
            <Heart className="w-5 h-5 text-red-400" />
            Понравившиеся треки
          </span>
          <ChevronRight className="w-5 h-5 text-gray-500" />
        </button>
      </section>

      {/* Выход */}
      <button
        type="button"
        onClick={handleLogout}
        className="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl border border-red-800/60 bg-red-950/40 text-red-300 hover:bg-red-900/50 hover:text-red-200 transition font-medium"
      >
        <LogOut className="w-5 h-5" />
        Выйти из аккаунта
      </button>
    </div>
  );
}
