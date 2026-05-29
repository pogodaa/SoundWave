// frontend/src/api/users.ts — API пользователя
import api from './client';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  avatar_url: string;
  role: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export const usersApi = {
  uploadAvatar: async (file: File): Promise<UserProfile> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.patch<UserProfile>('/users/me/avatar', formData, {
      headers: { 'Content-Type': undefined },
    });
    return data;
  },
};
