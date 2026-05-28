import { useAuth } from '../store/auth';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">
          Добро пожаловать, {user?.username || 'Пользователь'}
        </h1>
        <p className="text-gray-400 mt-2">
          Роль: {user?.role}. Здесь будет отображаться ваша музыкальная библиотека.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-gray-600 transition">
          <h3 className="text-xl font-semibold text-white mb-2">Плейлисты</h3>
          <p className="text-gray-400 text-sm">Управление коллекциями треков, создание и редактирование.</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-gray-600 transition">
          <h3 className="text-xl font-semibold text-white mb-2">История прослушиваний</h3>
          <p className="text-gray-400 text-sm">Хронология воспроизведённых треков и статистика.</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-gray-600 transition">
          <h3 className="text-xl font-semibold text-white mb-2">Рекомендации</h3>
          <p className="text-gray-400 text-sm">Персональные подборки на основе ML-модели.</p>
        </div>
      </div>
    </div>
  );
}