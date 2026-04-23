import api from './apiClient';
import type { JsonObject } from './apiErrors';

export interface ChatConversation {
  id: string;
  user_id: string;
  title: string;
  student_profile_json: JsonObject;
  lesson_frame_json: JsonObject;
  session_summary: string;
  created_at: string;
  updated_at: string;
}

export interface ChatConversationList {
  id: string;
  user_id: string;
  title: string;
  student_profile_json: JsonObject;
  lesson_frame_json: JsonObject;
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
  metadata_json: JsonObject;
  created_at: string;
}

export interface CreateConversationRequest {
  user_id: string;
  title: string;
}

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
  micro_tip?: string | null;
  self_check_prompt?: string | null;
  encouragement?: string | null;
  suggested_next_words: string[];
  topic?: string | null;
  intent?: string | null;
  rewrite?: string | null;
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
  lesson_frame: JsonObject;
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
    rewrite: string | null;
    corrections: Correction[];
    teacher_summary: string;
    strengths: string[];
    focus_areas: string[];
    next_practice: string[];
    reflection_question: string | null;
    encouragement: string | null;
  };
  student_profile: JsonObject;
  lesson_frame: JsonObject;
  session_summary: string;
}

export type WebSocketServerEvent =
  | DraftFeedbackEvent
  | AssistantStreamTokenEvent
  | AssistantDoneEvent
  | TeacherAnalysisEvent
  | PongEvent
  | ErrorEvent;

export const chatApi = {
  createConversation: async (requestData: CreateConversationRequest): Promise<ChatConversation> => {
    const response = await api.post('/api/v1/chat/conversations', requestData);
    return response.data;
  },

  listConversations: async (userId: string): Promise<ChatConversationList[]> => {
    const response = await api.get(`/api/v1/chat/conversations?user_id=${userId}`);
    return response.data;
  },

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

  deleteConversation: async (conversationId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/api/v1/chat/conversations/${conversationId}`);
    return response.data;
  },
};
