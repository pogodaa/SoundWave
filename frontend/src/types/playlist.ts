// frontend/src/types/playlist.ts — Типы плейлистов API

export interface PlaylistTrackRead {
  track_id: number;
  jamendo_id: number | null;
  title: string;
  artist_name: string | null;
  duration: number | null;
  audio_url: string;
  cover_url: string | null;
  genre: string | null;
  tags: string[];
  is_user_uploaded: boolean;
  is_available: boolean;
  position: number;
}

export interface PlaylistRead {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  share_token: string | null;
  created_at: string;
  updated_at: string;
  tracks: PlaylistTrackRead[];
}

export interface PlaylistCreatePayload {
  name: string;
  description?: string | null;
}
