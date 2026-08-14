import React from 'react';

const ChatCoachLoading: React.FC = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="mx-auto mb-4 size-11 animate-spin rounded-full border-2 border-white/10 border-t-primary-400"></div>
        <p className="text-sm text-gray-400">Preparando o Chat Coach…</p>
      </div>
    </div>
  );
};

export default ChatCoachLoading;
