import type { DraftFeedbackEvent, DraftIssue } from '../services/apiChat';

export interface ChatFeedbackState {
  barScore: number;
  issues: DraftIssue[];
  ghostSuggestion: string | null;
  microTip: string | null;
  selfCheckPrompt: string | null;
  encouragement: string | null;
  suggestedNextWords: string[];
  topic: string | null;
  intent: string | null;
  rewrite: string | null;
}

export interface ChatFeedbackSnapshot {
  barScore: number;
  issues: DraftIssue[];
}

export const initialChatFeedbackState: ChatFeedbackState = {
  barScore: 100,
  issues: [],
  ghostSuggestion: null,
  microTip: null,
  selfCheckPrompt: null,
  encouragement: null,
  suggestedNextWords: [],
  topic: null,
  intent: null,
  rewrite: null,
};

export const buildChatFeedbackState = (event: DraftFeedbackEvent): ChatFeedbackState => {
  return {
    barScore: event.bar_score_raw,
    issues: event.issues,
    ghostSuggestion: event.ghost_suggestion,
    microTip: event.micro_tip || null,
    selfCheckPrompt: event.self_check_prompt || null,
    encouragement: event.encouragement || null,
    suggestedNextWords: event.suggested_next_words || [],
    topic: event.topic || null,
    intent: event.intent || null,
    rewrite: event.rewrite || null,
  };
};

export const clearChatGhostSuggestion = (
  feedbackState: ChatFeedbackState
): ChatFeedbackState => {
  return {
    ...feedbackState,
    ghostSuggestion: null,
  };
};

export const buildChatFeedbackSnapshot = (
  feedbackState: ChatFeedbackState
): ChatFeedbackSnapshot => {
  return {
    barScore: feedbackState.barScore,
    issues: feedbackState.issues,
  };
};
