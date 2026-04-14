import React from 'react';

const ChatCoachLoading: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
        <p className="text-gray-400">Loading Chat Coach...</p>
      </div>
    </div>
  );
};

export default ChatCoachLoading;
