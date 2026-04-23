import React from 'react';

import ChatCoachComposer from './ChatCoachComposer';
import ChatCoachHeader from './ChatCoachHeader';
import ChatCoachLoading from './ChatCoachLoading';
import ChatCoachMessagePane from './ChatCoachMessagePane';
import { useChatCoachSession } from './useChatCoachSession';
import { LLMSettingsPanel } from './LLMSettingsPanel';
import AnalysisPanel from './AnalysisPanel';

interface ChatCoachSessionProps {
  userId: string;
  onExit: () => void;
}

const ChatCoachSession: React.FC<ChatCoachSessionProps> = ({ userId, onExit }) => {
  const {
    barScore,
    closeSettings,
    currentAssistantResponse,
    draftText,
    ghostSuggestion,
    handleDraftChange,
    handleExitClick,
    handleJumpToLatest,
    handleKeyDown,
    handleSendMessage,
    intent,
    isLoading,
    isSettingsOpen,
    isStreaming,
    issues,
    messageListRef,
    messages,
    microTip,
    selfCheckPrompt,
    encouragement,
    openSettings,
    rewrite,
    showJumpToLatest,
    suggestedNextWords,
    lessonFrame,
    studentProfile,
    teacherAnalysis,
    textareaRef,
    title,
    topic,
  } = useChatCoachSession(userId, onExit);

  if (isLoading) {
    return <ChatCoachLoading />;
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col overflow-hidden">
      <ChatCoachHeader
        title={title}
        onOpenSettings={openSettings}
        onExit={handleExitClick}
      />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0 relative">
          <ChatCoachMessagePane
            messages={messages}
            isStreaming={isStreaming}
            currentAssistantResponse={currentAssistantResponse}
            showJumpToLatest={showJumpToLatest}
            messageListRef={messageListRef}
            onJumpToLatest={handleJumpToLatest}
          />

          <ChatCoachComposer
            barScore={barScore}
            draftText={draftText}
            ghostSuggestion={ghostSuggestion}
            isStreaming={isStreaming}
            textareaRef={textareaRef}
            onDraftChange={handleDraftChange}
            onKeyDown={handleKeyDown}
            onSendMessage={handleSendMessage}
          />
        </div>

        {/* Analysis sidebar */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto p-4 min-h-0">
          <AnalysisPanel
            draftText={draftText}
            issues={issues}
            micro_tip={microTip}
            self_check_prompt={selfCheckPrompt}
            encouragement={encouragement}
            suggested_next_words={suggestedNextWords}
            topic={topic}
            intent={intent}
            rewrite={rewrite}
            lessonFrame={lessonFrame}
            studentProfile={studentProfile}
            teacherAnalysis={teacherAnalysis}
          />
        </div>
      </div>

      {/* LLM Settings Panel */}
      <LLMSettingsPanel
        userId={userId}
        isOpen={isSettingsOpen}
        onClose={closeSettings}
      />
    </div>
  );
};

export default ChatCoachSession;
