// frontend/src/pages/ProfilePage.tsx — Профиль пользователя

import { useRef, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Heart,
  ListMusic,
  LogOut,
  ChevronRight,
  Mail,
  Shield,
  Camera,
  Loader2,
  X,
  MoveUp,
  MoveDown,
  MoveLeft,
  MoveRight,
} from 'lucide-react';

import { useAuth } from '../store/auth';
import { useLikedTracksStore } from '../store/likedTracksStore';
import { usePlaylistsStore } from '../store/playlistsStore';
import { usersApi } from '../api/users';

const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024;
const AVATAR_OUTPUT_SIZE = 512;
const POSITION_STEP = 5;

interface AvatarPosition {
  x: number;
  y: number;
}

/** Загрузка изображения для обработки на canvas */
function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

/** Кадрирование под круглый аватар с учётом object-position */
async function buildCroppedAvatarFile(
  file: File,
  position: AvatarPosition
): Promise<File> {
  const url = URL.createObjectURL(file);
  try {
    const img = await loadImage(url);
    const canvas = document.createElement('canvas');
    canvas.width = AVATAR_OUTPUT_SIZE;
    canvas.height = AVATAR_OUTPUT_SIZE;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas не поддерживается');

    const scale = Math.max(
      AVATAR_OUTPUT_SIZE / img.width,
      AVATAR_OUTPUT_SIZE / img.height
    );
    const drawW = img.width * scale;
    const drawH = img.height * scale;
    const offsetX = (AVATAR_OUTPUT_SIZE - drawW) * (position.x / 100);
    const offsetY = (AVATAR_OUTPUT_SIZE - drawH) * (position.y / 100);
    ctx.drawImage(img, offsetX, offsetY, drawW, drawH);

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, 'image/jpeg', 0.92);
    });
    if (!blob) throw new Error('Не удалось обработать изображение');

    const baseName = file.name.replace(/\.[^.]+$/, '') || 'avatar';
    return new File([blob], `${baseName}.jpg`, { type: 'image/jpeg' });
  } finally {
    URL.revokeObjectURL(url);
  }
}

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
  const { user, logout, updateAvatar } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  const dragStateRef = useRef<{
    startX: number;
    startY: number;
    posX: number;
    posY: number;
  } | null>(null);

  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modalPreviewUrl, setModalPreviewUrl] = useState<string | null>(null);
  const [avatarPosition, setAvatarPosition] = useState<AvatarPosition>({ x: 50, y: 50 });
  const [isDraggingPreview, setIsDraggingPreview] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const likedCount = useLikedTracksStore((s) => s.likedIds.size);
  const playlistsCount = usePlaylistsStore((s) => s.playlists.length);

  // Освобождаем object URL при размонтировании
  useEffect(() => {
    return () => {
      if (modalPreviewUrl) {
        URL.revokeObjectURL(modalPreviewUrl);
      }
    };
  }, [modalPreviewUrl]);

  const clampPosition = (value: number) => Math.min(100, Math.max(0, value));

  const shiftAvatarPosition = useCallback((dx: number, dy: number) => {
    setAvatarPosition((prev) => ({
      x: clampPosition(prev.x + dx),
      y: clampPosition(prev.y + dy),
    }));
  }, []);

  const handlePreviewPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!modalPreviewUrl) return;
    e.preventDefault();
    previewRef.current?.setPointerCapture(e.pointerId);
    dragStateRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      posX: avatarPosition.x,
      posY: avatarPosition.y,
    };
    setIsDraggingPreview(true);
  };

  const handlePreviewPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragStateRef.current || !modalPreviewUrl) return;
    const dx = e.clientX - dragStateRef.current.startX;
    const dy = e.clientY - dragStateRef.current.startY;
    setAvatarPosition({
      x: clampPosition(dragStateRef.current.posX - dx * 0.15),
      y: clampPosition(dragStateRef.current.posY - dy * 0.15),
    });
  };

  const handlePreviewPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (previewRef.current?.hasPointerCapture(e.pointerId)) {
      previewRef.current.releasePointerCapture(e.pointerId);
    }
    dragStateRef.current = null;
    setIsDraggingPreview(false);
  };

  const handleLogout = () => {
    const confirmed = window.confirm(
      'Выйти из аккаунта? Текущая сессия будет завершена.'
    );
    if (confirmed) {
      logout();
    }
  };

  const resetAvatarModal = () => {
    if (modalPreviewUrl) {
      URL.revokeObjectURL(modalPreviewUrl);
    }
    setModalPreviewUrl(null);
    setSelectedFile(null);
    setAvatarPosition({ x: 50, y: 50 });
    setUploadError(null);
    dragStateRef.current = null;
    setIsDraggingPreview(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleOpenAvatarModal = () => {
    resetAvatarModal();
    setIsAvatarModalOpen(true);
  };

  const handleCloseAvatarModal = () => {
    resetAvatarModal();
    setIsAvatarModalOpen(false);
  };

  const handlePickAvatarFile = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setUploadError('Выберите файл изображения (JPEG, PNG, GIF, WebP).');
      return;
    }

    if (file.size > MAX_AVATAR_SIZE_BYTES) {
      setUploadError('Размер файла не должен превышать 5 МБ.');
      return;
    }

    setUploadError(null);
    setAvatarPosition({ x: 50, y: 50 });

    if (modalPreviewUrl) {
      URL.revokeObjectURL(modalPreviewUrl);
    }
    const objectUrl = URL.createObjectURL(file);
    setSelectedFile(file);
    setModalPreviewUrl(objectUrl);
  };

  const handleApplyAvatar = async () => {
    if (!selectedFile) {
      setUploadError('Сначала выберите изображение.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    try {
      const croppedFile = await buildCroppedAvatarFile(selectedFile, avatarPosition);
      const updatedUser = await usersApi.uploadAvatar(croppedFile);
      updateAvatar(updatedUser.avatar_url);
      handleCloseAvatarModal();
    } catch (err: unknown) {
      console.error('Ошибка загрузки аватара:', err);
      setUploadError('Не удалось загрузить аватар. Попробуйте другой файл.');
    } finally {
      setIsUploading(false);
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

  const avatarUrl = user.avatar_url ?? '/avatars/default1.png';
  const previewObjectPosition = `${avatarPosition.x}% ${avatarPosition.y}%`;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-white">Профиль</h1>

      {/* Карточка пользователя */}
      <section className="bg-gray-800 border border-gray-700 rounded-2xl overflow-hidden">
        <div className="h-24 bg-gradient-to-r from-blue-600/40 via-indigo-600/30 to-purple-600/20" />
        <div className="px-6 pb-6 -mt-12">
          <div className="flex flex-col sm:flex-row sm:items-end gap-4">
            <div className="flex flex-col items-start gap-2">
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
              <button
                type="button"
                onClick={handleOpenAvatarModal}
                className="flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300 transition"
              >
                <Camera className="w-4 h-4" />
                Сменить аватар
              </button>
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

      {/* Модальное окно смены аватара */}
      {isAvatarModalOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60"
          onClick={handleCloseAvatarModal}
        >
          <div
            className="bg-gray-800 border border-gray-700 rounded-2xl w-full max-w-md shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">Сменить аватар</h3>
              <button
                type="button"
                onClick={handleCloseAvatarModal}
                disabled={isUploading}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 transition"
                aria-label="Закрыть"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-4 py-3 text-center">
                <p className="text-sm font-medium text-blue-200">
                  Рекомендуемый размер: 512×512 px
                </p>
                <p className="text-xs text-blue-300/80 mt-1">Максимальный размер файла — 5 МБ</p>
              </div>

              {modalPreviewUrl ? (
                <div className="space-y-3">
                  <p className="text-xs text-gray-400 text-center">
                    Превью аватарки — перетащите изображение или используйте стрелки
                  </p>
                  <div
                    ref={previewRef}
                    className={`relative mx-auto w-40 h-40 rounded-full border-4 border-gray-600 bg-gray-700 overflow-hidden touch-none ${
                      isDraggingPreview ? 'cursor-grabbing' : 'cursor-grab'
                    }`}
                    onPointerDown={handlePreviewPointerDown}
                    onPointerMove={handlePreviewPointerMove}
                    onPointerUp={handlePreviewPointerUp}
                    onPointerCancel={handlePreviewPointerUp}
                  >
                    <img
                      src={modalPreviewUrl}
                      alt=""
                      className="w-full h-full object-cover select-none pointer-events-none"
                      style={{ objectPosition: previewObjectPosition }}
                      draggable={false}
                    />
                  </div>
                  <div className="flex items-center justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => shiftAvatarPosition(0, -POSITION_STEP)}
                      disabled={isUploading}
                      className="p-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-50"
                      aria-label="Сдвинуть вверх"
                    >
                      <MoveUp className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => shiftAvatarPosition(-POSITION_STEP, 0)}
                      disabled={isUploading}
                      className="p-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-50"
                      aria-label="Сдвинуть влево"
                    >
                      <MoveLeft className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => shiftAvatarPosition(POSITION_STEP, 0)}
                      disabled={isUploading}
                      className="p-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-50"
                      aria-label="Сдвинуть вправо"
                    >
                      <MoveRight className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => shiftAvatarPosition(0, POSITION_STEP)}
                      disabled={isUploading}
                      className="p-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-50"
                      aria-label="Сдвинуть вниз"
                    >
                      <MoveDown className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mx-auto w-40 h-40 rounded-full border-4 border-dashed border-gray-600 bg-gray-700/50 flex items-center justify-center">
                  <User className="w-16 h-16 text-gray-500" />
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleAvatarFileChange}
              />
              <button
                type="button"
                onClick={handlePickAvatarFile}
                disabled={isUploading}
                className="w-full py-2.5 rounded-xl border border-gray-600 text-gray-200 hover:bg-gray-700 disabled:opacity-50 transition text-sm"
              >
                {modalPreviewUrl ? 'Выбрать другое изображение' : 'Выбрать изображение'}
              </button>

              {uploadError && (
                <p className="text-sm text-red-400 text-center">{uploadError}</p>
              )}

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleCloseAvatarModal}
                  disabled={isUploading}
                  className="flex-1 py-2.5 rounded-xl border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-50 transition text-sm font-medium"
                >
                  Отмена
                </button>
                <button
                  type="button"
                  onClick={handleApplyAvatar}
                  disabled={isUploading || !selectedFile}
                  className="flex-1 py-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Загрузка…
                    </>
                  ) : (
                    'Применить'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
