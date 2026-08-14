import React from 'react';

import ScoreBar from './ScoreBar';
import InfoTooltip from './InfoTooltip';

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
    <div className="flex-shrink-0 border-t border-white/[0.07] bg-gray-900/90 px-3 py-3 backdrop-blur-xl sm:px-4">
      <div className="mx-auto max-w-5xl">
        <div className="mb-2">
          <ScoreBar score={barScore} size="md" />
        </div>

        <div className="relative">
          <textarea
            ref={textareaRef as React.RefObject<HTMLTextAreaElement>}
            value={draftText}
            onChange={onDraftChange}
            onKeyDown={onKeyDown}
            placeholder="Escreva sua mensagem…"
            className="input w-full resize-none pb-11 pr-24 text-sm leading-6"
            rows={2}
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
            className="btn btn-primary absolute bottom-2.5 right-2.5 min-h-9 px-4 text-xs"
          >
            Enviar
          </button>
        </div>

        <div className="mt-1.5 flex justify-end">
          <InfoTooltip label="Atalhos do chat">Enter envia · Shift+Enter cria uma linha · Tab aceita a sugestão fantasma.</InfoTooltip>
        </div>
      </div>
    </div>
  );
};

export default ChatCoachComposer;
