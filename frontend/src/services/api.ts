/** API service for FillTheWord frontend */

import axios from 'axios';

// Types based on API specification
export interface Gap {
  start: number;
  end: number;
}

export interface CardResponse {
  card_id: string;
  word_id: string;
  sentence_id: string;
  sentence: string;
  gap: Gap;
  sentence_translation: string;
  grammar_hint: string;
  memory_stage: string;
  is_new: boolean;
  audio_word_url: string;
  audio_sentence_url: string;
  sentence_source?: string | null;
}

export interface AnswerRequest {
  answer: string;
  response_time_ms: number;
}

export interface AnswerResponse {
  correct: boolean;
  correct_answer: string;
  sentence_full: string;
  quality: number;
  next_review_at: string;
}

export interface User {
  id: string;
  username: string;
  language_preference: string;
  // Note: target_language is stored in backend but not returned in list API
  created_at: string;
}

export interface CreateUserRequest {
  username: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
}

export interface UpdateUserRequest {
  username?: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
}

// API client
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.config?.baseURL + error.config?.url);
    return Promise.reject(error);
  }
);

// Card API endpoints
export const cardsApi = {
  // Get next card for study
  getNextCard: async (userId?: string, excludeCardId?: string): Promise<CardResponse> => {
    const params: any = {};
    if (userId) params.user_id = userId;
    if (excludeCardId) params.exclude_card_id = excludeCardId;
    const response = await api.get('/api/v1/cards/next-spec4', { params });
    return response.data;
  },

  // Submit answer for a card
  submitAnswer: async (
    cardId: string, 
    answerData: AnswerRequest,
    userId?: string
  ): Promise<AnswerResponse> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.post(
      '/api/v1/cards/' + cardId + '/answer', 
      answerData,
      { params }
    );
    return response.data;
  },
};

// User API endpoints
export const usersApi = {
  // List all users
  listUsers: async (): Promise<User[]> => {
    const response = await api.get('/api/v1/users/');
    return response.data;
  },

  // Create new user
  createUser: async (userData: CreateUserRequest): Promise<User> => {
    const response = await api.post('/api/v1/users/', userData);
    return response.data;
  },

  // Get user by ID
  getUser: async (userId: string): Promise<User> => {
    const response = await api.get(`/api/v1/users/${userId}`);
    return response.data;
  },

  // Update user
  updateUser: async (userId: string, userData: UpdateUserRequest): Promise<User> => {
    const response = await api.patch(`/api/v1/users/${userId}`, userData);
    return response.data;
  },

  // Delete user
  deleteUser: async (userId: string): Promise<{message: string; deleted_records: any}> => {
    const response = await api.delete(`/api/v1/users/${userId}`);
    return response.data;
  },
};

// Insights types
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

// Insights API
export const insightsApi = {
  // Get word insights
  getWordInsights: async (wordId: string): Promise<WordInsightResponse> => {
    const response = await api.get(`/api/v1/insights/word/${wordId}`);
    return response.data;
  },

  // Get word insights by card ID
  getWordInsightsByCard: async (cardId: string): Promise<WordInsightResponse> => {
    const response = await api.get(`/api/v1/insights/word-by-card/${cardId}`);
    return response.data;
  },

  // Get user theme performance
  getUserThemes: async (userId: string): Promise<ThemePerformanceResponse[]> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/themes`);
    return response.data;
  },

  // Get user daily progress
  getUserDailyStats: async (userId: string, days: number = 30): Promise<DailyStatsResponse> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/daily?days=${days}`);
    return response.data;
  },

  // Get recent performance
  getRecentPerformance: async (userId: string, responses: number = 30): Promise<RecentPerformanceResponse> => {
    const response = await api.get(`/api/v1/insights/user/${userId}/recent?responses=${responses}`);
    return response.data;
  },

  // Get word themes
  getWordThemes: async (wordId: string): Promise<string[]> => {
    const response = await api.get(`/api/v1/insights/word/${wordId}/themes`);
    return response.data;
  },
};

// Health check
export const healthApi = {
  checkHealth: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
