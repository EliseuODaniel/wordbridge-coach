/** Stats service for FillTheWord */

import api from './apiClient';

export interface StatsData {
  cards_total: number;
  new_count: number;
  learning_count: number;
  review_count: number;
  mature_count: number;
  reviews_today: number;
  accuracy_today: number;
  new_cards_today: number;
  upcoming_reviews: Record<string, number>;
}

export interface SettingsData {
  daily_new_limit: number;
  easiness_factor: number;
  word_goal_rank: number;
}

class StatsService {
  async getBasicStats(userId: string): Promise<StatsData> {
    const response = await api.get('/api/v1/stats/basic', {
      params: { user_id: userId },
    });
    return response.data;
  }

  async getSettings(userId: string): Promise<SettingsData> {
    const response = await api.get('/api/v1/settings/', {
      params: { user_id: userId },
    });
    return response.data;
  }

  async updateSettings(
    settings: Partial<SettingsData>,
    userId: string
  ): Promise<SettingsData> {
    const response = await api.patch('/api/v1/settings/', settings, {
      params: { user_id: userId },
    });
    return response.data;
  }
}

export const statsService = new StatsService();
