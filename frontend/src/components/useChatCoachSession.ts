import type React from 'react';
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';

import type {
  AssistantDoneEvent,
  AssistantStreamTokenEvent,
  ChatConversation,
  DraftFeedbackEvent,
  ErrorEvent,
  TeacherAnalysisEvent,
} from '../services/apiChat';
import type ChatWS from '../services/chatWs';
import {
  buildChatFeedbackSnapshot,
  buildChatFeedbackState,
  clearChatGhostSuggestion,
  initialChatFeedbackState,
  type ChatFeedbackSnapshot,
} from './chatCoachSessionFeedback';
import {
  buildMessageDisplay,
  isNearBottom,
  scrollElementToBottom,
  type MessageDisplay,
} from './chatCoachSessionHelpers';
import { bootstrapChatSession, createChatSessionWs } from './chatCoachSessionTransport';

interface Correction {
  mistake: string;
  fix: string;
  why: string;
}

export interface TeacherAnalysis {
  rewrite: string;
  corrections: Correction[];
  teacher_summary: string;
  next_practice: string[];
}

interface UseChatCoachSessionResult {
  barScore: number;
  currentAssistantResponse: string;
  draftText: string;
  ghostSuggestion: string | null;
  intent: string | null;
  isLoading: boolean;
  isSettingsOpen: boolean;
  isStreaming: boolean;
  issues: ReturnType<typeof buildChatFeedbackSnapshot>['issues'];
  messageListRef: React.RefObject<HTMLDivElement | null>;
  messages: MessageDisplay[];
  microTip: string | null;
  rewrite: string | null;
  showJumpToLatest: boolean;
  suggestedNextWords: string[];
  teacherAnalysis: TeacherAnalysis | null;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  title: string;
  topic: string | null;
  closeSettings: () => void;
  handleDraftChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleExitClick: () => void;
  handleJumpToLatest: () => void;
  handleKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handleSendMessage: () => void;
  openSettings: () => void;
}

export const useChatCoachSession = (
  userId: string,
  onExit: () => void
): UseChatCoachSessionResult => {
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<MessageDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [draftText, setDraftText] = useState('');
  const [feedbackState, setFeedbackState] = useState(initialChatFeedbackState);
  const [teacherAnalysis, setTeacherAnalysis] = useState<TeacherAnalysis | null>(null);
  const [isShowingLastFeedback, setIsShowingLastFeedback] = useState(false);
  const lastFeedbackRef = useRef<ChatFeedbackSnapshot | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentAssistantResponse, setCurrentAssistantResponse] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const chatWsRef = useRef<ChatWS | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const pinnedToBottomRef = useRef(true);
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);
  const autocompleteTimeoutRef = useRef<number | null>(null);

  const {
    barScore,
    issues,
    ghostSuggestion,
    microTip,
    suggestedNextWords,
    topic,
    intent,
    rewrite,
  } = feedbackState;

  const clearAutocompleteTimeout = useCallback(() => {
    if (autocompleteTimeoutRef.current) {
      window.clearTimeout(autocompleteTimeoutRef.current);
      autocompleteTimeoutRef.current = null;
    }
  }, []);

  const disconnectChatWs = useCallback(() => {
    if (chatWsRef.current) {
      chatWsRef.current.disconnect();
    }
  }, []);

  const focusTextarea = useCallback(() => {
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  }, []);

  const appendMessage = useCallback((role: MessageDisplay['role'], content: string) => {
    setMessages((prev) => [...prev, buildMessageDisplay(role, content)]);
  }, []);

  const clearComposerState = useCallback(() => {
    setDraftText('');
    setFeedbackState((prev) => clearChatGhostSuggestion(prev));
  }, []);

  const clearLastFeedbackSnapshot = useCallback(() => {
    setIsShowingLastFeedback(false);
    lastFeedbackRef.current = null;
  }, []);

  const scrollToBottom = useCallback(() => {
    scrollElementToBottom(messageListRef.current);
  }, []);

  useLayoutEffect(() => {
    if (pinnedToBottomRef.current) {
      scrollToBottom();
    }
  }, [messages.length, currentAssistantResponse, isStreaming, scrollToBottom]);

  useEffect(() => {
    const messageList = messageListRef.current;
    if (!messageList) return;

    const handleScroll = () => {
      const nearBottom = isNearBottom(messageList, 120);
      pinnedToBottomRef.current = nearBottom;
      setShowJumpToLatest(!nearBottom);
    };

    messageList.addEventListener('scroll', handleScroll);
    return () => messageList.removeEventListener('scroll', handleScroll);
  }, []);

  const handleJumpToLatest = useCallback(() => {
    pinnedToBottomRef.current = true;
    setShowJumpToLatest(false);
    scrollToBottom();
  }, [scrollToBottom]);

  const handleDraftFeedback = useCallback((event: DraftFeedbackEvent) => {
    setFeedbackState(buildChatFeedbackState(event));
  }, []);

  const handleStreamToken = useCallback((event: AssistantStreamTokenEvent) => {
    setIsStreaming(true);
    setCurrentAssistantResponse((prev) => prev + event.token);
  }, []);

  const handleAssistantDone = useCallback((event: AssistantDoneEvent) => {
    setIsStreaming(false);
    appendMessage('assistant', event.full_content);
    setCurrentAssistantResponse('');
    clearComposerState();
    focusTextarea();
  }, [appendMessage, clearComposerState, focusTextarea]);

  const handleError = useCallback((event: ErrorEvent) => {
    console.error('WebSocket error:', event);
  }, []);

  const handleTeacherAnalysis = useCallback((event: TeacherAnalysisEvent) => {
    console.log('[TEACHER_ANALYSIS_RX] Received event:', {
      type: event.type,
      conversation_id: event.conversation_id,
      analysis_keys: event.analysis ? Object.keys(event.analysis) : 'null',
      analysis: event.analysis,
    });
    setTeacherAnalysis(event.analysis);
  }, []);

  useEffect(() => {
    const initConversation = async () => {
      try {
        setIsLoading(true);

        const session = await bootstrapChatSession(userId);

        setConversation(session.conversation);
        setMessages(session.messages);

        chatWsRef.current = createChatSessionWs(session.conversation.id, {
          onDraftFeedback: handleDraftFeedback,
          onStreamToken: handleStreamToken,
          onAssistantDone: handleAssistantDone,
          onTeacherAnalysis: handleTeacherAnalysis,
          onError: handleError,
          onConnectionChange: (connected) => {
            console.log('WebSocket connection:', connected);
          },
        });
      } catch (error) {
        console.error('Failed to initialize conversation:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initConversation();

    return () => {
      disconnectChatWs();
      clearAutocompleteTimeout();
    };
  }, [
    clearAutocompleteTimeout,
    disconnectChatWs,
    handleAssistantDone,
    handleDraftFeedback,
    handleError,
    handleStreamToken,
    handleTeacherAnalysis,
    userId,
  ]);

  const handleDraftChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = event.target.value;
    setDraftText(newText);

    if (isShowingLastFeedback && newText.length > 0) {
      clearLastFeedbackSnapshot();
    }

    if (chatWsRef.current && conversation) {
      chatWsRef.current.sendDraftUpdate(newText, event.target.selectionStart);
    }

    clearAutocompleteTimeout();

    autocompleteTimeoutRef.current = window.setTimeout(() => {
      if (chatWsRef.current && newText.trim().length > 0) {
        chatWsRef.current.sendRequestAutocomplete(newText, 'soft');
      }
      autocompleteTimeoutRef.current = null;
    }, 1200);
  }, [clearAutocompleteTimeout, clearLastFeedbackSnapshot, conversation, isShowingLastFeedback]);

  const handleSendMessage = useCallback(() => {
    const trimmedText = draftText.trim();
    if (!trimmedText || !chatWsRef.current || isStreaming) {
      return;
    }

    appendMessage('user', trimmedText);
    lastFeedbackRef.current = buildChatFeedbackSnapshot(feedbackState);
    setIsShowingLastFeedback(true);
    chatWsRef.current.sendUserMessage(trimmedText);
    clearComposerState();
    clearAutocompleteTimeout();
    focusTextarea();
  }, [
    appendMessage,
    clearAutocompleteTimeout,
    clearComposerState,
    draftText,
    feedbackState,
    focusTextarea,
    isStreaming,
  ]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }

    if (event.key === 'Tab' && ghostSuggestion) {
      event.preventDefault();
      setDraftText((prev) => prev + ghostSuggestion);
      setFeedbackState((prev) => clearChatGhostSuggestion(prev));
    }
  }, [ghostSuggestion, handleSendMessage]);

  const handleExitClick = useCallback(() => {
    disconnectChatWs();
    clearAutocompleteTimeout();
    onExit();
  }, [clearAutocompleteTimeout, disconnectChatWs, onExit]);

  return {
    barScore,
    currentAssistantResponse,
    draftText,
    ghostSuggestion,
    intent,
    isLoading,
    isSettingsOpen,
    isStreaming,
    issues,
    messageListRef,
    messages,
    microTip,
    rewrite,
    showJumpToLatest,
    suggestedNextWords,
    teacherAnalysis,
    textareaRef,
    title: conversation?.title || 'Conversation',
    topic,
    closeSettings: () => setIsSettingsOpen(false),
    handleDraftChange,
    handleExitClick,
    handleJumpToLatest,
    handleKeyDown,
    handleSendMessage,
    openSettings: () => setIsSettingsOpen(true),
  };
};
