import api from './apiClient';

export interface WordInsightResponse {
  word_id: string;
  word: string;
  rank: number | null;
  coverage_pct: number | null;
  frequency_score: number | null;
  band: number | null;
  grammar_info: {
    part_of_speech: string;
    classification: string;
    grammar_hint: string;
  };
  frequency_description: string;
  coverage_description: string;
}

export interface ThemePerformanceResponse {
  theme_id: string;
  name: string;
  attempts: number;
  correct: number;
  accuracy: number;
  avg_response_time_ms: number;
  last_practiced_at: string | null;
  difficulty_words: string[];
}

export interface UserDailyStatsResponse {
  date: string;
  cards_answered: number;
  new_words_learned: number;
  reviews_done: number;
  accuracy: number;
  cumulative_mastered_words: number;
}

export interface RecentPerformanceResponse {
  recent_responses: Array<{
    card_id: string;
    word: string;
    was_correct: boolean;
    response_time_ms: number;
    quality: number;
    timestamp: string;
  }>;
  metrics: {
    accuracy_recent: number;
    avg_response_time_ms: number;
    trend_direction: 'improving' | 'declining' | 'stable' | 'insufficient_data' | 'no_data';
    session_cards: number;
  };
}

export interface DailyStatsResponse {
  daily_stats: UserDailyStatsResponse[];
  summary: {
    total_days: number;
    avg_daily_cards: number;
    avg_accuracy: number;
    total_new_words: number;
    vocabulary_growth: number;
  };
}

export const insightsApi = {
  getWordInsights: async (wordId: string): Promise<WordInsightResponse> => {
    const response = await api.get(`/api/v1/insights/word/${wordId}`);
    return response.data;
  },

  getWordInsightsByCard: async (cardId: string): Promise<WordInsightResponse> => {
    const response = await api.get(`/api/v1/insights/word-by-card/${cardId}`);
    return response.data;
  },

  getUserThemes: async (userId: string): Promise<ThemePerformanceResponse[]> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/themes`);
    return response.data;
  },

  getUserDailyStats: async (userId: string, days: number = 30): Promise<DailyStatsResponse> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/daily?days=${days}`);
    return response.data;
  },

  getRecentPerformance: async (userId: string, responses: number = 30): Promise<RecentPerformanceResponse> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/recent?responses=${responses}`);
    return response.data;
  },

  getWordThemes: async (wordId: string): Promise<string[]> => {
    const response = await api.get(`/api/v1/insights/word/${wordId}/themes`);
    return response.data;
  },
};
