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

// Lingvist mode types
export interface MicroProgress {
  current: number;
  total: number;
  new_words: number;
}

export interface LingvistCardResponse {
  card_id: string;
  word_id: string;
  sentence_id: string;
  word: string;
  sentence: string;
  gap: Gap;
  correct_answer: string;
  grammar_tag_pt: string;
  word_translation_pt: string | null;
  sentence_translation_pt: string | null;
  sentence_source?: string | null;
  is_new: boolean;
  micro_progress: MicroProgress;
  audio_word_url: string;
  audio_sentence_url: string;
}

export interface AnswerRequest {
  answer: string;
  response_time_ms: number;
  attempts?: number;
  hints_used?: number;
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
  mode: string;
  // Note: target_language is stored in backend but not returned in list API
  created_at: string;
}

export interface CreateUserRequest {
  username: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
  mode?: string;
}

export interface UpdateUserRequest {
  username?: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
  mode?: string;
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
  // Get next card for study (Spec4 mode)
  getNextCard: async (userId?: string, excludeCardId?: string): Promise<CardResponse> => {
    const params: any = {};
    if (userId) params.user_id = userId;
    if (excludeCardId) params.exclude_card_id = excludeCardId;
    const response = await api.get('/api/v1/cards/next-spec4', { params });
    return response.data;
  },

  // Get next card for Lingvist mode
  getNextLingvistCard: async (userId?: string, excludeCardId?: string): Promise<LingvistCardResponse> => {
    const params: any = {};
    if (userId) params.user_id = userId;
    if (excludeCardId) params.exclude_card_id = excludeCardId;
    const response = await api.get('/api/v1/cards/next-lingvist', { params });
    return response.data;
  },

  // Submit answer for a card
  submitAnswer: async (
    cardId: string,
    answerData: AnswerRequest,
    userId?: string
  ): Promise<AnswerResponse> => {
    const params = userId ? { user_id: userId } : {};
    // Ensure defaults for adaptive scheduler
    const payload = {
      ...answerData,
      attempts: answerData.attempts ?? 1,
      hints_used: answerData.hints_used ?? 0,
    };
    const response = await api.post(
      '/api/v1/cards/' + cardId + '/answer',
      payload,
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

// ============================================================================
// Chat Coach Types
// ============================================================================

export interface ChatConversation {
  id: string;
  user_id: string;
  title: string;
  student_profile_json: Record<string, any>;
  lesson_frame_json: Record<string, any>;
  session_summary: string;
  created_at: string;
  updated_at: string;
}

export interface ChatConversationList {
  id: string;
  user_id: string;
  title: string;
  student_profile_json: Record<string, any>;
  lesson_frame_json: Record<string, any>;
  session_summary: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface CreateConversationRequest {
  user_id: string;
  title: string;
}

// WebSocket Event Types (Client -> Server)
export interface DraftUpdateEvent {
  type: 'draft_update';
  conversation_id: string;
  draft_text: string;
  cursor: number;
  client_ts_ms: number;
}

export interface UserMessageEvent {
  type: 'user_message';
  conversation_id: string;
  content: string;
  client_ts_ms: number;
}

export interface RequestAutocompleteEvent {
  type: 'request_autocomplete';
  conversation_id: string;
  draft_text: string;
  client_ts_ms: number;
  mode: 'soft' | 'hard';
}

export interface PingEvent {
  type: 'ping';
  ts: number;
}

// WebSocket Event Types (Server -> Client)
export interface DraftFeedbackEvent {
  type: 'draft_feedback';
  conversation_id: string;
  bar_score_raw: number;
  bar_score_components: {
    spelling: number;
    grammar: number;
    syntax: number;
    lesson_alignment: number;
    naturalness: number;
  };
  lesson_alignment_score: number;
  issues: DraftIssue[];
  ghost_suggestion: string | null;
  micro_tip?: string | null;  // Helpful tip shown when issues=[]
  suggested_next_words: string[];  // Suggested next words to complete the phrase
  topic?: string | null;  // Detected conversation topic
  intent?: string | null;  // Detected user intent
  rewrite?: string | null;  // Suggested rewrite of entire draft
  server_ts_ms: number;
}

export interface DraftIssue {
  category: string;
  title: string;
  explanation: string;
  highlight_spans: Array<{ start: number; end: number }>;
  suggestions: string[];
}

export interface AssistantStreamTokenEvent {
  type: 'assistant_stream_token';
  conversation_id: string;
  token: string;
}

export interface AssistantDoneEvent {
  type: 'assistant_done';
  conversation_id: string;
  full_content: string;
  lesson_frame: Record<string, any>;
  summary_update: string;
}

export interface PongEvent {
  type: 'pong';
  ts: number;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
  code: string;
}

export interface Correction {
  mistake: string;
  fix: string;
  why: string;
}

export interface TeacherAnalysisEvent {
  type: 'teacher_analysis';
  conversation_id: string;
  user_message_id: string;
  analysis: {
    rewrite: string;
    corrections: Correction[];
    teacher_summary: string;
    next_practice: string[];
  };
}

export type WebSocketServerEvent =
  | DraftFeedbackEvent
  | AssistantStreamTokenEvent
  | AssistantDoneEvent
  | TeacherAnalysisEvent
  | PongEvent
  | ErrorEvent;

// ============================================================================
// Chat Coach API
// ============================================================================

export const chatApi = {
  // Create a new conversation
  createConversation: async (requestData: CreateConversationRequest): Promise<ChatConversation> => {
    const response = await api.post('/api/v1/chat/conversations', requestData);
    return response.data;
  },

  // List all conversations for a user
  listConversations: async (userId: string): Promise<ChatConversationList[]> => {
    const response = await api.get(`/api/v1/chat/conversations?user_id=${userId}`);
    return response.data;
  },

  // Get messages for a conversation
  getConversationMessages: async (
    conversationId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<ChatMessage[]> => {
    const response = await api.get(
      `/api/v1/chat/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },

  // Delete a conversation
  deleteConversation: async (conversationId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/api/v1/chat/conversations/${conversationId}`);
    return response.data;
  },
};

// ============================================================================
// LLM Profiles
// ============================================================================

export interface LLMProfile {
  id: string;
  name: string;
  provider: string;
  model: string;
  context_window: number;
  supports_streaming: boolean;
  supports_json: boolean;
  estimated_vram: string;
  quality_tier: string;
  speed_tier: string;
  description: string;
}

export interface UserLLMPreferences {
  id: string;
  user_id: string;
  chat_model_profile: string;
  teacher_model_profile: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateLLMPreferencesRequest {
  chat_model_profile?: string;
  teacher_model_profile?: string;
}

export const llmProfilesApi = {
  // Get all available LLM profiles
  getProfiles: async (userId?: string): Promise<{ profiles: LLMProfile[] }> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/api/v1/llm-profiles', { params });
    return response.data;
  },

  // Get current user's LLM preferences
  getMyPreferences: async (userId?: string): Promise<UserLLMPreferences> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/api/v1/users/me/llm-preferences', { params });
    return response.data;
  },

  // Update current user's LLM preferences
  updateMyPreferences: async (
    requestData: UpdateLLMPreferencesRequest,
    userId?: string
  ): Promise<UserLLMPreferences> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.put('/api/v1/users/me/llm-preferences', requestData, { params });
    return response.data;
  },
};

// ============================================================================
// Health Check
// ============================================================================

export const healthApi = {
  checkHealth: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
