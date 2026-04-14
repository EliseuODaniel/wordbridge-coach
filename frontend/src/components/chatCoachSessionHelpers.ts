import type { ChatMessage } from '../services/apiChat';

export interface MessageDisplay {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface BuildMessageDisplayOptions {
  id?: string;
  timestamp?: Date;
}

export const buildMessageDisplay = (
  role: MessageDisplay['role'],
  content: string,
  options: BuildMessageDisplayOptions = {}
): MessageDisplay => {
  return {
    id: options.id ?? Date.now().toString(),
    role,
    content,
    timestamp: options.timestamp ?? new Date(),
  };
};

export const mapConversationMessages = (messages: ChatMessage[]): MessageDisplay[] => {
  return messages
    .filter((msg) => msg.role !== 'system')
    .map((msg) =>
      buildMessageDisplay(msg.role as MessageDisplay['role'], msg.content, {
        id: msg.id,
        timestamp: new Date(msg.created_at),
      })
    );
};

export const isNearBottom = (element: HTMLDivElement | null, thresholdPx: number = 120): boolean => {
  if (!element) return false;
  const { scrollTop, scrollHeight, clientHeight } = element;
  return scrollHeight - scrollTop - clientHeight <= thresholdPx;
};

export const scrollElementToBottom = (element: HTMLDivElement | null): void => {
  if (!element) return;
  requestAnimationFrame(() => {
    element.scrollTop = element.scrollHeight;
  });
};

export const buildConversationTitle = (date: Date = new Date()): string => {
  return `Chat ${date.toLocaleDateString()}`;
};
