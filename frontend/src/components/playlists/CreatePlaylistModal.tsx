// frontend/src/components/playlists/CreatePlaylistModal.tsx — Модальное окно создания плейлиста

import { useState, FormEvent } from 'react';
import { X, Loader2 } from 'lucide-react';
import { usePlaylistsStore } from '../../store/playlistsStore';

interface CreatePlaylistModalProps {
  open: boolean;
  onClose: () => void;
  /** Вызывается после успешного создания (список уже обновлён в store) */
  onCreated?: () => void;
}

export default function CreatePlaylistModal({ open, onClose, onCreated }: CreatePlaylistModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const createPlaylist = usePlaylistsStore((s) => s.createPlaylist);

  if (!open) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await createPlaylist(trimmed, description.trim() || null);
      setName('');
      setDescription('');
      onCreated?.();
      onClose();
    } catch (err) {
      console.error(err);
      alert('Не удалось создать плейлист. Попробуйте снова.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-playlist-title"
        className="w-full max-w-md bg-gray-800 border border-gray-700 rounded-2xl shadow-xl overflow-hidden"
      >
        <div className="flex justify-between items-center px-5 py-4 border-b border-gray-700">
          <h2 id="create-playlist-title" className="text-lg font-semibold text-white">
            Новый плейлист
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-white transition"
            aria-label="Закрыть"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label htmlFor="pl-name" className="block text-sm font-medium text-gray-300 mb-1.5">
              Название <span className="text-red-400">*</span>
            </label>
            <input
              id="pl-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например, В дорогу"
              required
              maxLength={100}
              className="w-full px-4 py-3 rounded-xl bg-gray-900 border border-gray-600 text-white placeholder-gray-500 focus:border-blue-500 outline-none transition"
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="pl-desc" className="block text-sm font-medium text-gray-300 mb-1.5">
              Описание <span className="text-gray-500">(необязательно)</span>
            </label>
            <textarea
              id="pl-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Кратко опишите коллекцию..."
              rows={3}
              maxLength={500}
              className="w-full px-4 py-3 rounded-xl bg-gray-900 border border-gray-600 text-white placeholder-gray-500 focus:border-blue-500 outline-none resize-none transition"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-xl border border-gray-600 text-gray-300 hover:bg-gray-700 transition"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={!name.trim() || submitting}
              className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium flex items-center justify-center gap-2 transition"
            >
              {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
              Создать
            </button>
          </div>
          <p className="text-xs text-gray-500 text-center">
            Плейлист будет виден только вам (приватный).
          </p>
        </form>
      </div>
    </div>
  );
}
