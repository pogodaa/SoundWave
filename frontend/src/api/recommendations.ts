// frontend/src/api/recommendations.ts
import api from './client';
import { Track } from '../types/track';

export interface PersonalRecommendationsResponse {
  tracks: Track[];
  cold_start: boolean;
  used_popular_fallback?: boolean;
}

export const recommendationsApi = {
  getPersonal: async (limit: number = 20): Promise<PersonalRecommendationsResponse> => {
    const { data } = await api.get<PersonalRecommendationsResponse>(
      '/recommendations/personal',
      { params: { limit } },
    );
    return data;
  },
};
