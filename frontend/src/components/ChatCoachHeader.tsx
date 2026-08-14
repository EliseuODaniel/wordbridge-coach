import React from 'react';
import SessionHeader from './SessionHeader';
import type { TrainingMode } from './trainingModes';

interface ChatCoachHeaderProps {
  title: string;
  onOpenSettings: () => void;
  onExit: () => void;
  onModeChange?: (mode: TrainingMode) => void;
}

const ChatCoachHeader: React.FC<ChatCoachHeaderProps> = ({
  title,
  onOpenSettings,
  onExit,
  onModeChange,
}) => {
  return (
    <SessionHeader
      activeMode="chat"
      title="Chat Coach"
      description={title}
      onModeChange={onModeChange}
      onExit={onExit}
      actions={
        <button
          type="button"
          onClick={onOpenSettings}
          className="icon-button"
          title="Configurações do modelo"
          aria-label="Abrir configurações do modelo"
        >
          <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
          </svg>
        </button>
      }
    />
  );
};

export default ChatCoachHeader;
