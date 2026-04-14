import React from 'react';

import ScoreBar from './ScoreBar';

interface ChatCoachComposerProps {
  barScore: number;
  draftText: string;
  ghostSuggestion: string | null;
  isStreaming: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  onDraftChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: () => void;
}

const ChatCoachComposer: React.FC<ChatCoachComposerProps> = ({
  barScore,
  draftText,
  ghostSuggestion,
  isStreaming,
  textareaRef,
  onDraftChange,
  onKeyDown,
  onSendMessage,
}) => {
  return (
    <div className="border-t border-gray-700 bg-gray-800 px-4 py-4 flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="mb-3">
          <ScoreBar score={barScore} size="md" />
        </div>

        <div className="relative">
          <textarea
            ref={textareaRef as React.RefObject<HTMLTextAreaElement>}
            value={draftText}
            onChange={onDraftChange}
            onKeyDown={onKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="w-full px-4 py-3 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            rows={3}
            autoFocus
          />

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

          <button
            onClick={onSendMessage}
            disabled={!draftText.trim() || isStreaming}
            className="absolute bottom-3 right-3 px-4 py-1.5 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          💡 Type to see real-time feedback • Press Enter to send • Tab accepts ghost suggestions
        </p>
      </div>
    </div>
  );
};

export default ChatCoachComposer;
