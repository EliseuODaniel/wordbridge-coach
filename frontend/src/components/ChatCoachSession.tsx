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

      <div className="min-h-0 flex-1 overflow-hidden px-2 pb-2 pt-1 sm:px-3 sm:pb-3">
        <div
          className="grid h-full min-h-0 w-full grid-cols-1 overflow-hidden rounded-2xl border border-white/[0.07] bg-gray-950/20 shadow-panel lg:grid-cols-[minmax(0,1fr)_clamp(22rem,28vw,28rem)]"
          data-testid="chat-coach-layout"
        >
          <div className="relative flex min-h-0 min-w-0 flex-col" data-testid="chat-coach-conversation">
            <ChatCoachMessagePane
              messages={messages}
              isStreaming={isStreaming}
              currentAssistantResponse={currentAssistantResponse}
              showJumpToLatest={showJumpToLatest}
              messageListRef={messageListRef}
              onJumpToLatest={handleJumpToLatest}
            />

            <details className="mx-3 mb-2 rounded-xl border border-white/[0.07] bg-gray-800/80 lg:hidden">
              <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-300">Feedback de escrita</summary>
              <div className="max-h-[45vh] overflow-y-auto border-t border-white/[0.07] p-3">{renderAnalysis()}</div>
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

          <aside
            className="hidden min-h-0 min-w-0 overflow-x-hidden overflow-y-auto border-l border-white/[0.07] bg-gray-800/65 p-3 backdrop-blur-xl lg:block"
            data-testid="chat-coach-feedback"
          >
            {renderAnalysis()}
          </aside>
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
