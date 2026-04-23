import api from './apiClient';

interface CardQueryParams {
  user_id?: string;
  exclude_card_id?: string;
}

export interface Gap {
  start: number;
  end: number;
}

export interface LearningContext {
  mode: string;
  cefr_level: string;
  support_level: string;
  current_focus: string;
  session_goal: string;
  topic: string;
  feedback_language: string;
  why_this_now: string;
  retention_signal?: string | null;
  review_pressure?: string | null;
  difficulty_signal?: string | null;
  recommended_pace?: string | null;
  next_mode_hint?: string | null;
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
  learning_context?: LearningContext | null;
}

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
  learning_context?: LearningContext | null;
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

const buildCardQueryParams = (userId?: string, excludeCardId?: string): CardQueryParams => {
  const params: CardQueryParams = {};
  if (userId) params.user_id = userId;
  if (excludeCardId) params.exclude_card_id = excludeCardId;
  return params;
};

export const cardsApi = {
  getNextCard: async (userId?: string, excludeCardId?: string): Promise<CardResponse> => {
    const response = await api.get('/api/v1/cards/next-spec4', {
      params: buildCardQueryParams(userId, excludeCardId),
    });
    return response.data;
  },

  getNextLingvistCard: async (userId?: string, excludeCardId?: string): Promise<LingvistCardResponse> => {
    const response = await api.get('/api/v1/cards/next-lingvist', {
      params: buildCardQueryParams(userId, excludeCardId),
    });
    return response.data;
  },

  submitAnswer: async (
    cardId: string,
    answerData: AnswerRequest,
    userId?: string
  ): Promise<AnswerResponse> => {
    const params = userId ? { user_id: userId } : {};
    const payload = {
      ...answerData,
      attempts: answerData.attempts ?? 1,
      hints_used: answerData.hints_used ?? 0,
    };
    const response = await api.post(`/api/v1/cards/${cardId}/answer`, payload, { params });
    return response.data;
  },
};
