import React from 'react';

import ChatCoachComposer from './ChatCoachComposer';
import ChatCoachHeader from './ChatCoachHeader';
import ChatCoachLoading from './ChatCoachLoading';
import ChatCoachMessagePane from './ChatCoachMessagePane';
import { useChatCoachSession } from './useChatCoachSession';
import { LLMSettingsPanel } from './LLMSettingsPanel';
import AnalysisPanel from './AnalysisPanel';
import type { TrainingMode } from './trainingModes';

interface ChatCoachSessionProps {
  userId: string;
  onExit: () => void;
  onModeChange?: (mode: TrainingMode) => void;
}

const ChatCoachSession: React.FC<ChatCoachSessionProps> = ({ userId, onExit, onModeChange }) => {
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

  const renderAnalysis = () => (
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
  );

  return (
    <div className="fixed inset-0 flex flex-col overflow-hidden bg-gray-900">
      <ChatCoachHeader
        title={title}
        onOpenSettings={openSettings}
        onExit={handleExitClick}
        onModeChange={onModeChange}
      />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Chat area */}
        <div className="relative flex min-h-0 min-w-0 flex-1 flex-col">
          <ChatCoachMessagePane
            messages={messages}
            isStreaming={isStreaming}
            currentAssistantResponse={currentAssistantResponse}
            showJumpToLatest={showJumpToLatest}
            messageListRef={messageListRef}
            onJumpToLatest={handleJumpToLatest}
          />

          <details className="mx-3 mb-2 rounded-xl border border-white/[0.07] bg-white/[0.03] lg:hidden">
            <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-300">Feedback de escrita</summary>
            <div className="max-h-56 overflow-y-auto border-t border-white/[0.07] p-3">{renderAnalysis()}</div>
          </details>

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
        <aside className="hidden min-h-0 w-[19rem] overflow-y-auto border-l border-white/[0.07] bg-gray-800/65 p-3 backdrop-blur-xl lg:block">
          {renderAnalysis()}
        </aside>
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
