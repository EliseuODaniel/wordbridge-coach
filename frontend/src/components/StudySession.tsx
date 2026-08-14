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
import SessionHeader from './SessionHeader';
import type { TrainingMode } from './trainingModes';

interface StudySessionProps {
  userId?: string;
  onModeChange?: (mode: TrainingMode) => void;
  onExit?: () => void;
}

const StudySession: React.FC<StudySessionProps> = ({ userId, onModeChange, onExit }) => {
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
    <div className="relative min-h-screen">
      <SessionHeader
        activeMode="spec4"
        title="Revisão guiada"
        description="Recuperação ativa • repetição espaçada • contexto"
        onModeChange={onModeChange}
        onExit={onExit}
      />
      <main className="relative mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8" data-testid="study-container">
        {stats && settings && (
          <SessionCounter
            stats={stats}
            dailyNewLimit={settings.daily_new_limit}
          />
        )}

        {currentCard ? (
          <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="space-y-5">
              <CardDisplay
                card={currentCard}
                onPlayWordAudio={handlePlayWordAudio}
                onPlaySentenceAudio={handlePlaySentenceAudio}
                loadingAudio={loadingAudio}
              />
              <div className="surface-card p-4 sm:p-5">
                <p className="mb-3 text-center text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">Complete a lacuna</p>
                <AnswerInput
                  key={`${currentCard.card_id}:${feedback?.correct ? 'resolved' : 'active'}`}
                  onSubmit={handleSubmit}
                  isSubmitting={isSubmitting}
                  placeholder="Digite a palavra que falta"
                  feedback={feedback ? {
                    correct: feedback.correct,
                    correctAnswer: feedback.correct_answer
                  } : null}
                  cardId={currentCard?.card_id}
                />
              </div>
              {feedback && (
                <FeedbackMessage
                  feedback={{ correct: feedback.correct, correctAnswer: feedback.correct_answer, sentenceFull: feedback.sentence_full, quality: feedback.quality, nextReview: feedback.next_review_at }}
                  hint={currentCard.grammar_hint}
                  attempts={attempts}
                />
              )}
            </section>

            <aside className="space-y-4 xl:sticky xl:top-28" aria-label="Contexto pedagógico">
              <LearningContextPanel context={currentCard.learning_context} />
              <CompetencyPanel competency={currentCard.competency} />
              <ContentContextBadges context={currentCard.content_context} />
            </aside>
          </div>
        ) : (
          <div className="surface-panel py-20 text-center">
            <div className="mx-auto mb-5 size-11 animate-spin rounded-full border-2 border-white/10 border-t-primary-400" />
            <p className="text-gray-300">
              {isSubmitting ? 'Preparando a próxima atividade…' : 'Nenhuma atividade disponível agora.'}
            </p>
            {isSubmitting && (
              <p className="mt-2 text-sm text-gray-500">Consultando seu progresso…</p>
            )}
          </div>
        )}

        <div data-testid="insights-container">
          <InsightsSection
            userId={userId!}
            cardId={currentCard?.card_id}
            wordId={currentCard?.word_id}
            refreshTrigger={refreshTrigger}
          />
        </div>

        <div className="mt-8 text-center text-xs text-gray-500">
          <p>Pressione <kbd className="mx-1 rounded-md border border-white/10 bg-white/[0.05] px-2 py-1 font-mono text-gray-300">Enter</kbd> para conferir</p>
        </div>
      </main>
    </div>
  );
};

export default StudySession;
