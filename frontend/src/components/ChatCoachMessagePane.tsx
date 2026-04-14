import React from 'react';

import type { MessageDisplay } from './chatCoachSessionHelpers';

interface ChatCoachMessagePaneProps {
  messages: MessageDisplay[];
  isStreaming: boolean;
  currentAssistantResponse: string;
  showJumpToLatest: boolean;
  messageListRef: React.RefObject<HTMLDivElement | null>;
  onJumpToLatest: () => void;
}

const ChatCoachMessagePane: React.FC<ChatCoachMessagePaneProps> = ({
  messages,
  isStreaming,
  currentAssistantResponse,
  showJumpToLatest,
  messageListRef,
  onJumpToLatest,
}) => {
  return (
    <>
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 min-h-0" ref={messageListRef as React.RefObject<HTMLDivElement>}>
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

      {showJumpToLatest && (
        <button
          onClick={onJumpToLatest}
          className="absolute bottom-20 left-1/2 transform -translate-x-1/2 px-4 py-2 bg-primary-600 text-white text-sm rounded-full shadow-lg hover:bg-primary-700 transition-colors flex items-center gap-2 z-10"
        >
          <span>↓</span>
          <span>Jump to latest</span>
        </button>
      )}
    </>
  );
};

export default ChatCoachMessagePane;
