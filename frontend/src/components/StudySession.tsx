/** Main Study Session Component */

import React from 'react';
import CardDisplay from './CardDisplay';
import AnswerInput from './AnswerInput';
import FeedbackMessage from './FeedbackMessage';
import SessionCounter from './SessionCounter';
import InsightsSection from './InsightsSection';
import LearningContextPanel from './LearningContextPanel';
import CompetencyPanel from './CompetencyPanel';
import ContentContextBadges from './ContentContextBadges';
import { useStudySession } from './useStudySession';

type TrainingMode = 'spec4' | 'lingvist' | 'chat';

interface StudySessionProps {
  userId?: string;
  onModeChange?: (mode: TrainingMode) => void;
}

const StudySession: React.FC<StudySessionProps> = ({ userId, onModeChange }) => {
  const {
    attempts,
    currentCard,
    feedback,
    isSubmitting,
    loadingAudio,
    stats,
    settings,
    refreshTrigger,
    handlePlaySentenceAudio,
    handlePlayWordAudio,
    handleSubmit,
  } = useStudySession(userId);

  
return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="container mx-auto px-4" data-testid="study-container">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="text-center flex-1">
            <h1 className="text-4xl font-extrabold text-gray-100 mb-2">
              WordBridge Coach
            </h1>
            <p className="text-gray-500 text-sm">
              Spec4 Mode • Multiple Choice Training
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onModeChange?.('lingvist')}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition text-sm"
            >
              Switch to Lingvist ✍️
            </button>
          </div>
        </div>

        {/* Session Counter */}
        {stats && settings && (
          <SessionCounter
            stats={stats}
            dailyNewLimit={settings.daily_new_limit}
          />
        )}

        {/* Main Content */}
        {currentCard ? (
          <div className="space-y-8">
            <LearningContextPanel context={currentCard.learning_context} />
            <CompetencyPanel competency={currentCard.competency} />
            <ContentContextBadges context={currentCard.content_context} />

            {/* Card Display */}
            <CardDisplay
              card={currentCard}
              onPlayWordAudio={handlePlayWordAudio}
              onPlaySentenceAudio={handlePlaySentenceAudio}
              loadingAudio={loadingAudio}
            />

            {/* Answer Input and Feedback */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Answer Input - Always visible */}
              <AnswerInput
                key={`${currentCard.card_id}:${feedback?.correct ? 'resolved' : 'active'}`}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                placeholder="Type the missing word..."
                feedback={feedback ? {
                  correct: feedback.correct,
                  correctAnswer: feedback.correct_answer
                } : null}
                cardId={currentCard?.card_id}
              />

              {/* Feedback Message - Visible when available */}
              {feedback && (
                <FeedbackMessage
                  feedback={{
                    correct: feedback.correct,
                    correctAnswer: feedback.correct_answer,
                    sentenceFull: feedback.sentence_full,
                    quality: feedback.quality,
                    nextReview: feedback.next_review_at,
                  }}
                  hint={currentCard.grammar_hint}
                  attempts={attempts}
                />
              )}
            </div>
          </div>
        ) : (
          /* Loading State */
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-400">
              {isSubmitting ? 'Loading your next card...' : 'No cards available. Please try refreshing.'}
            </p>
            {isSubmitting && (
              <p className="text-gray-500 text-sm mt-2">
                Checking with server...
              </p>
            )}
          </div>
        )}

        {/* Insights Section - Added below the main practice area */}
        <div data-testid="insights-container">
          <InsightsSection
            userId={userId!}
            cardId={currentCard?.card_id}
            wordId={currentCard?.word_id}
            refreshTrigger={refreshTrigger}
          />
        </div>

        {/* Keyboard Shortcuts Help */}
        <div className="text-center mt-8 text-sm text-gray-400">
          <p>Press <kbd className="px-2 py-1 bg-gray-700 text-gray-100 rounded">Enter</kbd> to submit answer</p>
        </div>
      </div>
    </div>
  );
};

export default StudySession;
