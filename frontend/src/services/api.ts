/** API service facade for FillTheWord frontend */

import api from './apiClient';

export {
  getApiErrorCode,
  getApiErrorMessage,
  getApiErrorStatus,
  isRetryableApiError,
} from './apiErrors';
export type { ApiErrorDetailObject, ApiErrorResponse, JsonObject } from './apiErrors';

export { cardsApi } from './apiCards';
export type {
  AnswerRequest,
  AnswerResponse,
  CardResponse,
  Gap,
  LingvistCardResponse,
  MicroProgress,
} from './apiCards';

export { usersApi } from './apiUsers';
export type { CreateUserRequest, UpdateUserRequest, User } from './apiUsers';

export { insightsApi } from './apiInsights';
export type {
  DailyStatsResponse,
  RecentPerformanceResponse,
  ThemePerformanceResponse,
  UserDailyStatsResponse,
  WordInsightResponse,
} from './apiInsights';

export { chatApi } from './apiChat';
export type {
  AssistantDoneEvent,
  AssistantStreamTokenEvent,
  ChatConversation,
  ChatConversationList,
  ChatMessage,
  Correction,
  CreateConversationRequest,
  DraftFeedbackEvent,
  DraftIssue,
  DraftUpdateEvent,
  ErrorEvent,
  PingEvent,
  PongEvent,
  RequestAutocompleteEvent,
  TeacherAnalysisEvent,
  UserMessageEvent,
  WebSocketServerEvent,
} from './apiChat';

export { llmProfilesApi } from './apiLlmProfiles';
export type {
  LLMProfile,
  UpdateLLMPreferencesRequest,
  UserLLMPreferences,
} from './apiLlmProfiles';

export { healthApi } from './apiHealth';

export default api;
