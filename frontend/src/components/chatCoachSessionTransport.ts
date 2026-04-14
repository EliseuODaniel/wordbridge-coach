import { chatApi, type ChatConversation, type ChatMessage } from '../services/apiChat';
import ChatWS, { type ChatWSConfig } from '../services/chatWs';
import {
  buildConversationTitle,
  mapConversationMessages,
  type MessageDisplay,
} from './chatCoachSessionHelpers';

export interface ChatSessionBootstrapResult {
  conversation: ChatConversation;
  messages: MessageDisplay[];
}

export const bootstrapChatSession = async (userId: string): Promise<ChatSessionBootstrapResult> => {
  const conversation = await chatApi.createConversation({
    user_id: userId,
    title: buildConversationTitle(),
  });

  const loadedMessages: ChatMessage[] = await chatApi.getConversationMessages(conversation.id);

  return {
    conversation,
    messages: mapConversationMessages(loadedMessages),
  };
};

export const createChatSessionWs = (
  conversationId: string,
  config: Omit<ChatWSConfig, 'conversationId'>
): ChatWS => {
  return new ChatWS({
    conversationId,
    ...config,
  });
};
