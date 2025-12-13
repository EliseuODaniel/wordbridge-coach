/** Stats service for FillTheWord */

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
}

class StatsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  async getBasicStats(userId?: string): Promise<StatsData> {
    try {
      const url = `${this.baseUrl}/api/v1/stats/basic${userId ? `?user_id=${userId}` : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  }

  async getSettings(userId?: string): Promise<SettingsData> {
    try {
      const url = `${this.baseUrl}/api/v1/settings/${userId ? `?user_id=${userId}` : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching settings:', error);
      throw error;
    }
  }

  async updateSettings(
    settings: Partial<SettingsData>,
    userId?: string
  ): Promise<SettingsData> {
    try {
      const url = `${this.baseUrl}/api/v1/settings/${userId ? `?user_id=${userId}` : ''}`;
      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`Failed to update settings: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating settings:', error);
      throw error;
    }
  }
}

export const statsService = new StatsService();