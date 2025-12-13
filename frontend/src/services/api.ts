/** API service for FillTheWord frontend */

import axios from 'axios';

// Types based on API specification
export interface Gap {
  start: number;
  end: number;
}

export interface CardResponse {
  card_id: string;
  sentence: string;
  gap: Gap;
  sentence_translation: string;
  grammar_hint: string;
  memory_stage: string;
  audio_word_url: string;
  audio_sentence_url: string;
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
  getNextCard: async (userId?: string): Promise<CardResponse> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/api/v1/cards/next', { params });
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

// Health check
export const healthApi = {
  checkHealth: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
