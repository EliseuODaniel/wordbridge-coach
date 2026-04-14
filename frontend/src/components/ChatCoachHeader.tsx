import React from 'react';

interface ChatCoachHeaderProps {
  title: string;
  onOpenSettings: () => void;
  onExit: () => void;
}

const ChatCoachHeader: React.FC<ChatCoachHeaderProps> = ({
  title,
  onOpenSettings,
  onExit,
}) => {
  return (
    <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-3">
        <span className="text-2xl">💬</span>
        <div>
          <h1 className="text-lg font-semibold text-gray-100">Chat Coach</h1>
          <p className="text-xs text-gray-400">{title}</p>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={onOpenSettings}
          className="px-3 py-1.5 bg-gray-700 text-gray-300 text-sm rounded hover:bg-gray-600 transition-colors"
          title="LLM Settings"
        >
          ⚙️
        </button>
        <button
          onClick={onExit}
          className="px-3 py-1.5 bg-gray-700 text-gray-300 text-sm rounded hover:bg-gray-600 transition-colors"
        >
          Exit
        </button>
      </div>
    </div>
  );
};

export default ChatCoachHeader;
