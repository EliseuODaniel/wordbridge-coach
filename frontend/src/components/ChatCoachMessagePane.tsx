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
      <div className="mx-auto min-h-0 w-full max-w-[50rem] flex-1 space-y-3 overflow-y-auto px-4 py-4 sm:px-5" ref={messageListRef as React.RefObject<HTMLDivElement>}>
        {messages.length === 0 ? (
          <div className="mx-auto flex h-full max-w-md flex-col items-center justify-center py-8 text-center">
            <span className="mb-4 inline-flex size-12 items-center justify-center rounded-2xl bg-violet-400/10 text-violet-200">
              <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M7 18.5 3.5 21v-5.2A8.2 8.2 0 0 1 2 11c0-5 4.5-9 10-9s10 4 10 9-4.5 9-10 9a11 11 0 0 1-5-.5Z" /><path strokeLinecap="round" d="M7.5 10.5h9M7.5 14h5.5" /></svg>
            </span>
            <h2 className="text-lg font-semibold text-white">Comece uma conversa</h2>
            <p className="mt-2 text-sm leading-6 text-gray-400">Escreva no idioma que está estudando. O coach acompanha sua produção e oferece apoio durante a conversa.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[82%] rounded-2xl px-4 py-2.5 sm:max-w-[72%] ${
                  msg.role === 'user'
                    ? 'rounded-br-md bg-primary-500 text-white shadow-glow'
                    : 'rounded-bl-md border border-white/[0.07] bg-white/[0.045] text-gray-100'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="mt-1 text-[10px] opacity-55">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}

        {isStreaming && currentAssistantResponse && (
          <div className="flex justify-start">
            <div className="max-w-[82%] rounded-2xl rounded-bl-md border border-white/[0.07] bg-white/[0.045] px-4 py-2.5 text-gray-100 sm:max-w-[72%]">
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
          className="btn btn-primary absolute bottom-24 left-1/2 z-10 min-h-10 -translate-x-1/2 rounded-full px-4 text-xs"
        >
          <span>↓</span>
          <span>Ir para a última mensagem</span>
        </button>
      )}
    </>
  );
};

export default ChatCoachMessagePane;
