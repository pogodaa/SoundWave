// frontend/src/types/track.ts — Типы для треков и ответов API
export interface Track {
  id: number;
  jamendo_id: number | null;
  title: string;
  artist_name: string;
  album_name: string | null;
  duration: number | null;
  audio_url: string;
  cover_url: string | null;
  genre: string | null;
  tags: string[];
  is_user_uploaded: boolean;
  created_at: string;
  updated_at?: string | null;
  is_available?: boolean;
  /** Опционально: подставляется в списках, где уже известно состояние */
  is_liked?: boolean;
}

export interface TrackSearchResponse {
  items: Track[];
  total: number;
}

export interface PlayUrlResponse {
  audio_url: string;
}
