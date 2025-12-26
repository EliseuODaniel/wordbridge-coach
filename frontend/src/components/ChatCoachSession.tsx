/**
 * ChatCoachSession Component
 *
 * Main Chat Coach mode component with full flow:
 * - Create/load conversation
 * - Real-time draft feedback via WebSocket
 * - Score bar with EMA smoothing
 * - Streaming responses from AI teacher
 * - Issue analysis panel
 */

import React, { useState, useEffect, useRef } from 'react';
import { chatApi } from '../services/api';
import ChatWS from '../services/chatWs';
import type {
  ChatConversation,
  DraftFeedbackEvent,
  AssistantStreamTokenEvent,
  AssistantDoneEvent,
  TeacherAnalysisEvent,
  ErrorEvent,
} from '../services/api';
import ScoreBar from './ScoreBar';
import AnalysisPanel from './AnalysisPanel';

interface Correction {
  mistake: string;
  fix: string;
  why: string;
}

interface TeacherAnalysis {
  rewrite: string;
  corrections: Correction[];
  teacher_summary: string;
  next_practice: string[];
}

interface ChatCoachSessionProps {
  userId: string;
  onExit: () => void;
}

interface MessageDisplay {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatCoachSession: React.FC<ChatCoachSessionProps> = ({ userId, onExit }) => {
  // Conversation state
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<MessageDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Input state
  const [draftText, setDraftText] = useState('');

  // Real-time feedback state
  const [barScore, setBarScore] = useState<number>(100);
  const [issues, setIssues] = useState<any[]>([]);
  const [ghostSuggestion, setGhostSuggestion] = useState<string | null>(null);
  const [microTip, setMicroTip] = useState<string | null>(null);
  const [suggestedNextWords, setSuggestedNextWords] = useState<string[]>([]);
  const [topic, setTopic] = useState<string | null>(null);
  const [intent, setIntent] = useState<string | null>(null);
  const [rewrite, setRewrite] = useState<string | null>(null);
  const [teacherAnalysis, setTeacherAnalysis] = useState<TeacherAnalysis | null>(null);

  // Track if we're showing feedback from a sent message
  const [isShowingLastFeedback, setIsShowingLastFeedback] = useState<boolean>(false);
  const lastFeedbackRef = useRef<{ barScore: number; issues: any[] } | null>(null);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentAssistantResponse, setCurrentAssistantResponse] = useState('');

  // WebSocket ref
  const chatWsRef = useRef<ChatWS | null>(null);

  // Input ref
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Message list ref for auto-scroll
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const isUserScrolledUpRef = useRef(false);

  // Autocomplete idle timer
  const autocompleteTimeoutRef = useRef<number | null>(null);

  /**
   * Initialize conversation
   */
  useEffect(() => {
    const initConversation = async () => {
      try {
        setIsLoading(true);

        // Create new conversation
        const newConversation = await chatApi.createConversation({
          user_id: userId,
          title: `Chat ${new Date().toLocaleDateString()}`,
        });

        setConversation(newConversation);

        // Load existing messages
        const loadedMessages = await chatApi.getConversationMessages(newConversation.id);
        const userMessages: MessageDisplay[] = loadedMessages
          .filter((msg) => msg.role !== 'system')
          .map((msg) => ({
            id: msg.id,
            role: msg.role as 'user' | 'assistant',
            content: msg.content,
            timestamp: new Date(msg.created_at),
          }));

        setMessages(userMessages);

        // Connect WebSocket
        connectWebSocket(newConversation.id);
      } catch (error) {
        console.error('Failed to initialize conversation:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initConversation();

    // Cleanup on unmount
    return () => {
      if (chatWsRef.current) {
        chatWsRef.current.disconnect();
      }
      if (autocompleteTimeoutRef.current) {
        window.clearTimeout(autocompleteTimeoutRef.current);
      }
    };
  }, [userId]);

  /**
   * Auto-scroll to bottom when new messages arrive (if user is near bottom)
   */
  useEffect(() => {
    const messageList = messageListRef.current;
    if (!messageList) return;

    // Check if user is near bottom (within 100px)
    const isNearBottom = () => {
      const { scrollTop, scrollHeight, clientHeight } = messageList;
      return scrollHeight - scrollTop - clientHeight < 100;
    };

    // Scroll to bottom if near bottom or first message
    if (isNearBottom() || messages.length === 0) {
      messageList.scrollTop = messageList.scrollHeight;
    }
  }, [messages]);

  /**
   * Track scroll position to detect if user scrolled up
   */
  useEffect(() => {
    const messageList = messageListRef.current;
    if (!messageList) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = messageList;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      isUserScrolledUpRef.current = distanceFromBottom > 100;
    };

    messageList.addEventListener('scroll', handleScroll);
    return () => messageList.removeEventListener('scroll', handleScroll);
  }, []);

  /**
   * Connect WebSocket for real-time communication
   */
  const connectWebSocket = (conversationId: string) => {
    chatWsRef.current = new ChatWS({
      conversationId,
      onDraftFeedback: handleDraftFeedback,
      onStreamToken: handleStreamToken,
      onAssistantDone: handleAssistantDone,
      onTeacherAnalysis: handleTeacherAnalysis,
      onError: handleError,
      onConnectionChange: (connected) => {
        console.log('WebSocket connection:', connected);
      },
    });
  };

  /**
   * Handle draft feedback from server
   */
  const handleDraftFeedback = (event: DraftFeedbackEvent) => {
    setBarScore(event.bar_score_raw);
    setIssues(event.issues);
    setGhostSuggestion(event.ghost_suggestion);
    setMicroTip(event.micro_tip || null);
    setSuggestedNextWords(event.suggested_next_words || []);
    setTopic(event.topic || null);
    setIntent(event.intent || null);
    setRewrite(event.rewrite || null);
  };

  /**
   * Handle streaming token from assistant
   */
  const handleStreamToken = (event: AssistantStreamTokenEvent) => {
    setIsStreaming(true);
    setCurrentAssistantResponse((prev) => prev + event.token);
  };

  /**
   * Handle assistant done streaming
   */
  const handleAssistantDone = (event: AssistantDoneEvent) => {
    setIsStreaming(false);

    // Add assistant message to list
    const assistantMessage: MessageDisplay = {
      id: Date.now().toString(),
      role: 'assistant',
      content: event.full_content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setCurrentAssistantResponse('');
    setDraftText('');
    setGhostSuggestion(null);

    // Refocus textarea for next message
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  };

  /**
   * Handle WebSocket error
   */
  const handleError = (event: ErrorEvent) => {
    console.error('WebSocket error:', event);
  };

  /**
   * Handle teacher analysis from server
   */
  const handleTeacherAnalysis = (event: TeacherAnalysisEvent) => {
    console.log('Teacher analysis received:', event);
    setTeacherAnalysis(event.analysis);
  };

  /**
   * Handle draft text change with real-time feedback
   */
  const handleDraftChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setDraftText(newText);

    // Clear "last message feedback" when user starts typing new message
    if (isShowingLastFeedback && newText.length > 0) {
      setIsShowingLastFeedback(false);
      lastFeedbackRef.current = null;
    }

    // Send draft_update via WebSocket
    if (chatWsRef.current && conversation) {
      chatWsRef.current.sendDraftUpdate(newText, e.target.selectionStart);
    }

    // Schedule autocomplete (if user stops typing for 1.2s)
    if (autocompleteTimeoutRef.current) {
      window.clearTimeout(autocompleteTimeoutRef.current);
    }

    autocompleteTimeoutRef.current = window.setTimeout(() => {
      if (chatWsRef.current && newText.trim().length > 0) {
        chatWsRef.current.sendRequestAutocomplete(newText, 'soft');
      }
    }, 1200);
  };

  /**
   * Handle key press (Enter to send, Shift+Enter for new line)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }

    // TAB to accept ghost suggestion
    if (e.key === 'Tab' && ghostSuggestion) {
      e.preventDefault();
      setDraftText((prev) => prev + ghostSuggestion);
      setGhostSuggestion(null);
    }
  };

  /**
   * Send user message
   */
  const handleSendMessage = () => {
    const trimmedText = draftText.trim();
    if (!trimmedText || !chatWsRef.current || isStreaming) {
      return;
    }

    // Add user message to list immediately
    const userMessage: MessageDisplay = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmedText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Store current feedback as "last message feedback"
    lastFeedbackRef.current = { barScore, issues };
    setIsShowingLastFeedback(true);

    // Send via WebSocket
    chatWsRef.current.sendUserMessage(trimmedText);

    // Clear input (but KEEP barScore and issues!)
    setDraftText('');
    setGhostSuggestion(null);

    // Clear autocomplete timeout
    if (autocompleteTimeoutRef.current) {
      window.clearTimeout(autocompleteTimeoutRef.current);
    }

    // Keep textarea focused for next message
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  };

  /**
   * Handle exit button
   */
  const handleExitClick = () => {
    if (chatWsRef.current) {
      chatWsRef.current.disconnect();
    }
    onExit();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading Chat Coach...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-2xl">💬</span>
          <div>
            <h1 className="text-lg font-semibold text-gray-100">Chat Coach</h1>
            <p className="text-xs text-gray-400">
              {conversation?.title || 'Conversation'}
            </p>
          </div>
        </div>

        <button
          onClick={handleExitClick}
          className="px-3 py-1.5 bg-gray-700 text-gray-300 text-sm rounded hover:bg-gray-600 transition-colors"
        >
          Exit
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 min-h-0" ref={messageListRef}>
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 mb-2">
                  👋 Start practicing with your AI teacher!
                </p>
                <p className="text-gray-500 text-sm">
                  Type a message below to begin. You'll get real-time feedback as you type.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}

            {/* Streaming response */}
            {isStreaming && currentAssistantResponse && (
              <div className="flex justify-start">
                <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-700 text-gray-100">
                  <p className="text-sm whitespace-pre-wrap">
                    {currentAssistantResponse}
                    <span className="animate-pulse">▊</span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="border-t border-gray-700 bg-gray-800 px-4 py-4 flex-shrink-0">
            <div className="max-w-4xl mx-auto">
              {/* Score bar */}
              <div className="mb-3">
                <ScoreBar score={barScore} size="md" />
              </div>

              {/* Text input with ghost suggestion */}
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={draftText}
                  onChange={handleDraftChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                  className="w-full px-4 py-3 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                  rows={3}
                  autoFocus
                />

                {/* Ghost suggestion */}
                {ghostSuggestion && (
                  <div className="absolute bottom-3 left-4 pointer-events-none">
                    <span className="text-gray-500 text-sm">
                      {draftText}
                      <span className="text-gray-600">
                        {ghostSuggestion}
                        <span className="text-xs ml-2">(Tab to accept)</span>
                      </span>
                    </span>
                  </div>
                )}

                {/* Send button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!draftText.trim() || isStreaming}
                  className="absolute bottom-3 right-3 px-4 py-1.5 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Send
                </button>
              </div>

              {/* Hint */}
              <p className="text-xs text-gray-500 mt-2">
                💡 Type to see real-time feedback • Press Enter to send • Tab accepts ghost suggestions
              </p>
            </div>
          </div>
        </div>

        {/* Analysis sidebar */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto p-4 min-h-0">
          <AnalysisPanel
            draftText={draftText}
            issues={issues}
            micro_tip={microTip}
            suggested_next_words={suggestedNextWords}
            topic={topic}
            intent={intent}
            rewrite={rewrite}
            teacherAnalysis={teacherAnalysis}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatCoachSession;
