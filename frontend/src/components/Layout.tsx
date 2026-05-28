// frontend/src/components/Layout.tsx — Глобальный лейаут: хедер, навигация, Outlet, глобальный плеер
import { memo } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { Music, User, Heart, UserCircle } from 'lucide-react';
import Player from './player/Player';

// Мемоизация: предотвращает перерисовку Layout при изменении состояния внутри страниц
const Layout = memo(function Layout() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Шапка сайта — фиксированная высота */}
      <header className="bg-gray-800 border-b border-gray-700 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Левая часть: логотип и навигация */}
            <div className="flex items-center space-x-6">
              <div 
                className="flex items-center cursor-pointer"
                onClick={() => navigate('/')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && navigate('/')}
              >
                <Music className="h-8 w-8 text-blue-500" />
                <span className="ml-2 text-xl font-bold text-white">SoundWave</span>
              </div>

              <nav className="flex items-center space-x-4">
                <button
                  onClick={() => navigate('/')}
                  className="text-gray-300 hover:text-white transition px-3 py-2 rounded-md text-sm font-medium"
                >
                  Главная
                </button>
                <button
                  onClick={() => navigate('/tracks')}
                  className="text-gray-300 hover:text-white transition px-3 py-2 rounded-md text-sm font-medium"
                >
                  Треки
                </button>
                <button
                  onClick={() => navigate('/playlists')}
                  className="text-gray-300 hover:text-white transition px-3 py-2 rounded-md text-sm font-medium"
                >
                  Плейлисты
                </button>
                <button
                  onClick={() => navigate('/liked')}
                  className="text-gray-300 hover:text-white transition px-3 py-2 rounded-md text-sm font-medium flex items-center gap-1.5"
                >
                  <Heart className="w-4 h-4 text-red-400" />
                  Понравившиеся
                </button>
                <button
                  onClick={() => navigate('/profile')}
                  className="text-gray-300 hover:text-white transition px-3 py-2 rounded-md text-sm font-medium flex items-center gap-1.5"
                >
                  <UserCircle className="w-4 h-4" />
                  Профиль
                </button>
              </nav>
            </div>

            {/* Правая часть: переход в профиль */}
            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="flex items-center text-gray-300 hover:text-white transition px-3 py-2 rounded-lg hover:bg-gray-700"
            >
              <User className="h-5 w-5 mr-2" />
              <span className="text-sm font-medium">{user?.username ?? 'Профиль'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Основной контент — растёт, чтобы заполнить пространство между хедером и плеером */}
      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      
      {/* Глобальный аудиоплеер — фиксирован снизу, не перекрывает контент */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 z-50">
        <Player />
      </div>
      
      {/* Отступ снизу, чтобы последний элемент контента не уходил под плеер */}
      <div className="h-24 flex-shrink-0" />
    </div>
  );
});

export default Layout;