/** Compact adaptive cloze study session. */

import React from 'react';
import InlineGapInput from './InlineGapInput';
import HintPanel from './HintPanel';
import LearningContextPanel from './LearningContextPanel';
import { isTranslationAvailable } from './lingvistSessionHelpers';
import { useLingvistSession } from './useLingvistSession';
import SpeakingPractice from './SpeakingPractice';
import CompetencyPanel from './CompetencyPanel';
import ContentContextBadges from './ContentContextBadges';
import SessionHeader from './SessionHeader';
import InfoTooltip from './InfoTooltip';
import type { TrainingMode } from './trainingModes';


interface LingvistSessionProps {
  userId?: string;
  onExit?: () => void;
  onModeChange?: (mode: TrainingMode) => void;
}


const LingvistSession: React.FC<LingvistSessionProps> = ({ userId, onExit, onModeChange }) => {
  const {
    attempts,
    audioError,
    currentCard,
    errorMessage,
    feedback,
    hintLevel,
    isInputLocked,
    isPlayingAudio,
    isSubmitting,
    handlePlaySentenceAudio,
    handlePlayWordAudio,
    handleRetryLoad,
    handleSubmit,
    handleUserEdit,
  } = useLingvistSession(userId);

  return (
    <div className="relative min-h-screen">
      <SessionHeader
        activeMode="lingvist"
        title="Cloze adaptativo"
        description="Produção escrita • pistas progressivas • áudio"
        onModeChange={onModeChange}
        onExit={onExit}
      />

      <main className="relative mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        {currentCard ? (
          <div className="space-y-4">
            <section className="surface-card flex flex-wrap items-center gap-3 px-4 py-3" aria-label="Progresso da sessão">
              <div className="min-w-0 flex-1">
                <div className="mb-1.5 flex items-center justify-between gap-3 text-[11px] text-gray-500">
                  <span>Progresso da sessão</span>
                  <strong className="font-semibold tabular-nums text-gray-300">{currentCard.micro_progress.current} / {currentCard.micro_progress.total}</strong>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-300 to-primary-400 transition-all duration-300"
                    style={{ width: `${(currentCard.micro_progress.current / currentCard.micro_progress.total) * 100}%` }}
                  />
                </div>
              </div>
              <span className="status-pill whitespace-nowrap">{currentCard.micro_progress.new_words} novas</span>
              <InfoTooltip label="Sobre o progresso">O microciclo equilibra palavras novas e revisões para manter a sessão curta e previsível.</InfoTooltip>
            </section>

            <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_330px]">
              <section className="space-y-4">
                <article className="surface-panel p-4 sm:p-5">
                  <header className="flex flex-wrap items-center gap-2 border-b border-white/[0.07] pb-3">
                    <span className="status-pill border-teal-400/20 bg-teal-400/10 text-teal-200">
                      {currentCard.grammar_tag_pt !== 'UNK' ? currentCard.grammar_tag_pt : 'palavra'}
                    </span>
                    {currentCard.is_new && <span className="status-pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">nova</span>}
                    <span className="ml-auto text-[11px] text-gray-500">Digite e pressione Enter</span>
                  </header>

                  <div className="py-7 sm:py-9">
                    <InlineGapInput
                      key={currentCard.card_id}
                      sentence={currentCard.sentence}
                      gap={currentCard.gap}
                      correctAnswer={currentCard.correct_answer}
                      onSubmit={handleSubmit}
                      onUserEdit={handleUserEdit}
                      disabled={isSubmitting || isPlayingAudio}
                      isCorrect={feedback?.correct === true}
                      isIncorrect={feedback?.correct === false}
                    />
                  </div>

                  <footer className="flex flex-wrap items-center gap-2 border-t border-white/[0.07] pt-3">
                    <p className="min-w-0 flex-1 truncate text-xs italic text-gray-500" title={currentCard.sentence_translation_pt ?? ''}>
                      {isTranslationAvailable(currentCard.sentence_translation_pt) ? currentCard.sentence_translation_pt : 'Tradução indisponível'}
                    </p>
                    <button onClick={handlePlayWordAudio} className="btn btn-secondary min-h-10 px-3 text-xs" disabled={isPlayingAudio}>Ouvir palavra</button>
                    <button onClick={handlePlaySentenceAudio} className="btn btn-secondary min-h-10 px-3 text-xs" disabled={isPlayingAudio}>Ouvir frase</button>
                  </footer>
                </article>

                <HintPanel
                  correctAnswer={currentCard.correct_answer}
                  wordTranslationPt={currentCard.word_translation_pt}
                  sentenceTranslationPt={currentCard.sentence_translation_pt}
                  hintLevel={hintLevel}
                />

                {feedback && (
                  <div className={`flex items-center gap-3 rounded-2xl border p-3 ${feedback.correct ? 'border-emerald-400/25 bg-emerald-400/10' : 'border-red-400/25 bg-red-400/10'}`}>
                    <span className={`inline-flex size-9 shrink-0 items-center justify-center rounded-xl font-bold ${feedback.correct ? 'bg-emerald-400/15 text-emerald-200' : 'bg-red-400/15 text-red-200'}`}>
                      {feedback.correct ? '✓' : '×'}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className={`text-sm font-semibold ${feedback.correct ? 'text-emerald-100' : 'text-red-100'}`}>
                        {feedback.correct ? 'Correto!' : 'Tente novamente'}
                      </div>
                      {!feedback.correct && <div className="text-xs text-gray-400">Tentativa {attempts} · nível de pista {hintLevel}</div>}
                    </div>
                    {isPlayingAudio && <span className="status-pill">reproduzindo áudio</span>}
                  </div>
                )}

                {errorMessage && (
                  <div className="flex items-center gap-3 rounded-2xl border border-amber-400/25 bg-amber-400/10 p-3 text-sm text-amber-100">
                    <span className="font-bold">!</span><span className="min-w-0 flex-1">{errorMessage}</span>
                  </div>
                )}

                {audioError && (
                  <div className="flex items-center gap-3 rounded-2xl border border-orange-400/20 bg-orange-400/10 p-3 text-xs text-orange-100">
                    Áudio indisponível nesta tentativa.
                    <InfoTooltip label="Detalhes do erro de áudio">{audioError}</InfoTooltip>
                  </div>
                )}

                <SpeakingPractice
                  key={currentCard.card_id}
                  expectedText={currentCard.sentence.replace('___', currentCard.correct_answer)}
                />
              </section>

              <aside className="space-y-3 xl:sticky xl:top-24" aria-label="Contexto da atividade">
                <LearningContextPanel context={currentCard.learning_context} />
                <CompetencyPanel competency={currentCard.competency} />
                <ContentContextBadges context={currentCard.content_context} />

                <section className="surface-soft p-3" aria-label="Traduções">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-gray-500">Traduções</h2>
                    <InfoTooltip label="Sobre as traduções">Use a tradução como apoio de significado, sem tentar reproduzir a estrutura palavra por palavra.</InfoTooltip>
                  </div>
                  <dl className="space-y-2 text-sm">
                    <div className="grid grid-cols-[54px_1fr] gap-2"><dt className="text-xs text-gray-500">Palavra</dt><dd className="truncate text-gray-200">{isTranslationAvailable(currentCard.word_translation_pt) ? currentCard.word_translation_pt : 'Indisponível'}</dd></div>
                    <div className="grid grid-cols-[54px_1fr] gap-2"><dt className="text-xs text-gray-500">Frase</dt><dd className="line-clamp-2 text-gray-300">{isTranslationAvailable(currentCard.sentence_translation_pt) ? currentCard.sentence_translation_pt : 'Indisponível'}</dd></div>
                  </dl>
                </section>
              </aside>

              {import.meta.env.DEV && (
                <div className="sr-only" aria-hidden="true">
                  correct_answer: {currentCard.correct_answer}; word: {currentCard.word}; hintLevel: {hintLevel}; attempts: {attempts}; isLocked: {isInputLocked ? 'yes' : 'no'}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="surface-panel py-20 text-center">
            {errorMessage ? (
              <>
                <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-2xl bg-red-400/10 text-xl font-bold text-red-200">!</div>
                <h2 className="text-lg font-semibold text-white">Não foi possível carregar a atividade</h2>
                <p className="mx-auto mt-2 max-w-md text-sm text-gray-400">{errorMessage}</p>
                <button onClick={handleRetryLoad} className="btn btn-primary mt-5">Tentar novamente</button>
              </>
            ) : (
              <>
                <div className="mx-auto mb-5 size-11 animate-spin rounded-full border-2 border-white/10 border-t-primary-400" />
                <p className="text-sm text-gray-400">Preparando a próxima frase…</p>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
};


export default LingvistSession;
