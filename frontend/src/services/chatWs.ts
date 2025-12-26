/**
 * WebSocket Client for Chat Coach Mode
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Throttling for draft_update events
 * - Event handlers for all server events
 * - Heartbeat/ping-pong mechanism
 */

import type {
  DraftUpdateEvent,
  UserMessageEvent,
  RequestAutocompleteEvent,
  PingEvent,
  WebSocketServerEvent,
  DraftFeedbackEvent,
  AssistantStreamTokenEvent,
  AssistantDoneEvent,
  TeacherAnalysisEvent,
  PongEvent,
  ErrorEvent,
} from './api';

export type { WebSocketServerEvent };

export interface ChatWSConfig {
  conversationId: string;
  onDraftFeedback?: (event: DraftFeedbackEvent) => void;
  onStreamToken?: (event: AssistantStreamTokenEvent) => void;
  onAssistantDone?: (event: AssistantDoneEvent) => void;
  onTeacherAnalysis?: (event: TeacherAnalysisEvent) => void;
  onPong?: (event: PongEvent) => void;
  onError?: (event: ErrorEvent) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export class ChatWS {
  private ws: WebSocket | null = null;
  private conversationId: string;
  private config: ChatWSConfig;
  private reconnectTimeout: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelays = [500, 1000, 2000, 5000]; // Exponential backoff (ms)
  private isIntentionalClose = false;

  // Throttling for draft_update events
  private lastDraftUpdate = 0;
  private draftUpdateThrottleMs = 50; // Client-side throttle (backend has 90ms)

  // Heartbeat
  private heartbeatInterval: number | null = null;
  private heartbeatIntervalMs = 30000; // Send ping every 30s

  constructor(config: ChatWSConfig) {
    this.conversationId = config.conversationId;
    this.config = config;
    this.connect();
  }

  /**
   * Connect to WebSocket server
   */
  private connect(): void {
    if (this.ws) {
      return; // Already connected
    }

    const wsUrl = this.getWebSocketUrl();
    console.log('[ChatWS] Connecting to:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[ChatWS] Connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.config.onConnectionChange?.(true);
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.ws.onclose = (event) => {
        console.log('[ChatWS] Disconnected:', event.code, event.reason);
        this.stopHeartbeat();
        this.ws = null;
        this.config.onConnectionChange?.(false);

        // Attempt reconnection if not intentional
        if (!this.isIntentionalClose) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[ChatWS] Error:', error);
      };
    } catch (error) {
      console.error('[ChatWS] Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Get WebSocket URL for the conversation
   */
  private getWebSocketUrl(): string {
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = apiBase.replace('http://', 'ws://').replace('https://', 'wss://');
    return `${wsUrl}/api/v1/chat/ws/${this.conversationId}`;
  }

  /**
   * Handle incoming message from server
   */
  private handleMessage(data: string): void {
    try {
      const event: WebSocketServerEvent = JSON.parse(data);

      switch (event.type) {
        case 'draft_feedback':
          this.config.onDraftFeedback?.(event);
          break;

        case 'assistant_stream_token':
          this.config.onStreamToken?.(event);
          break;

        case 'assistant_done':
          this.config.onAssistantDone?.(event);
          break;

        case 'teacher_analysis':
          console.log('[ChatWS] teacher_analysis event received, calling onTeacherAnalysis callback');
          this.config.onTeacherAnalysis?.(event);
          break;

        case 'pong':
          this.config.onPong?.(event);
          break;

        case 'error':
          this.config.onError?.(event);
          break;

        default:
          console.warn('[ChatWS] Unknown event type:', event);
      }
    } catch (error) {
      console.error('[ChatWS] Failed to parse message:', error, data);
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[ChatWS] Max reconnection attempts reached');
      return;
    }

    // Get delay based on attempt number (cycle through delays)
    const delayIndex = Math.min(this.reconnectAttempts, this.reconnectDelays.length - 1);
    const delay = this.reconnectDelays[delayIndex];

    console.log(`[ChatWS] Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Start heartbeat ping interval
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      this.sendPing();
    }, this.heartbeatIntervalMs);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Send draft_update event (with throttling)
   */
  sendDraftUpdate(draftText: string, cursor: number): void {
    const now = Date.now();

    // Client-side throttle (backend has additional 90ms throttle)
    if (now - this.lastDraftUpdate < this.draftUpdateThrottleMs) {
      return;
    }

    this.lastDraftUpdate = now;

    const event: DraftUpdateEvent = {
      type: 'draft_update',
      conversation_id: this.conversationId,
      draft_text: draftText,
      cursor,
      client_ts_ms: now,
    };

    this.send(event);
  }

  /**
   * Send user_message event
   */
  sendUserMessage(content: string): void {
    const event: UserMessageEvent = {
      type: 'user_message',
      conversation_id: this.conversationId,
      content,
      client_ts_ms: Date.now(),
    };

    this.send(event);
  }

  /**
   * Send request_autocomplete event
   */
  sendRequestAutocomplete(draftText: string, mode: 'soft' | 'hard' = 'soft'): void {
    const event: RequestAutocompleteEvent = {
      type: 'request_autocomplete',
      conversation_id: this.conversationId,
      draft_text: draftText,
      client_ts_ms: Date.now(),
      mode,
    };

    this.send(event);
  }

  /**
   * Send ping event
   */
  private sendPing(): void {
    const event: PingEvent = {
      type: 'ping',
      ts: Date.now(),
    };

    this.send(event);
  }

  /**
   * Send event to server
   */
  private send(event: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(event));
    } else {
      console.warn('[ChatWS] Cannot send message, WebSocket not connected:', event);
    }
  }

  /**
   * Close WebSocket connection (intentional)
   */
  disconnect(): void {
    this.isIntentionalClose = true;

    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Stop heartbeat
    this.stopHeartbeat();

    // Close WebSocket
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }

    this.config.onConnectionChange?.(false);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export default ChatWS;
