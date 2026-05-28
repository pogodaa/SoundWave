// frontend/src/utils/playlistTrackMap.ts — PlaylistTrackRead → Track для TrackCard и плеера

import type { PlaylistTrackRead } from '../types/playlist';
import type { Track } from '../types/track';

/** Преобразует элемент плейлиста из API в тип Track приложения */
export function playlistTrackReadToTrack(pt: PlaylistTrackRead): Track {
  return {
    id: pt.track_id,
    jamendo_id: pt.jamendo_id,
    title: pt.title,
    artist_name: pt.artist_name || 'Неизвестный исполнитель',
    album_name: null,
    duration: pt.duration ?? null,
    audio_url: pt.audio_url,
    cover_url: pt.cover_url || '/default-cover.jpg',
    genre: pt.genre,
    tags: pt.tags ?? [],
    is_user_uploaded: pt.is_user_uploaded,
    created_at: '',
    is_available: pt.is_available !== false,
  };
}
