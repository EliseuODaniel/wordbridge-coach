/** Lingvist Mode Study Session Component */

import React from 'react';
import InlineGapInput from './InlineGapInput';
import HintPanel from './HintPanel';
import { isTranslationAvailable } from './lingvistSessionHelpers';
import { useLingvistSession } from './useLingvistSession';

type TrainingMode = 'spec4' | 'lingvist' | 'chat';

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
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="text-center flex-1">
            <h1 className="text-4xl font-extrabold text-gray-100 mb-2">
              Lingvist Mode
            </h1>
            <p className="text-gray-500 text-sm">
              Cloze Deletion • Progressive Hints • Auto-submit
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onModeChange?.('spec4')}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition text-sm"
            >
              Switch to Spec4 🎯
            </button>
            <button
              onClick={onExit}
              className="px-4 py-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700 transition text-sm"
              disabled={isPlayingAudio}
            >
              Exit
            </button>
          </div>
        </div>

        {/* Exit Button (removed - now in header) */}

        {/* Main Content */}
        {currentCard ? (
          <div className="space-y-6">
            {/* Micro Progress Bar */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-sm">Session Progress</span>
                <span className="text-gray-100 font-semibold">
                  {currentCard.micro_progress.current} / {currentCard.micro_progress.total}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${(currentCard.micro_progress.current / currentCard.micro_progress.total) * 100}%`
                  }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {currentCard.micro_progress.new_words} new words
              </div>
            </div>

            {/* Grammar Tag & Badges */}
            <div className="flex gap-2 flex-wrap items-center">
              {currentCard.grammar_tag_pt !== 'UNK' ? (
                <span className="px-3 py-1 bg-blue-900 text-blue-200 text-sm rounded flex items-center gap-1">
                  <span>{currentCard.grammar_tag_pt}</span>
                  <span className="text-xs">↓</span>
                </span>
              ) : (
                <span className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded flex items-center gap-1">
                  <span>palavra</span>
                  <span className="text-xs">↓</span>
                </span>
              )}
              {currentCard.is_new && (
                <span className="px-3 py-1 bg-green-900 text-green-200 text-sm rounded">
                  New
                </span>
              )}
              {currentCard.sentence_source && (
                <span className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded">
                  {currentCard.sentence_source}
                </span>
              )}
            </div>

            {/* Card Display with Inline Input */}
            <div className="bg-gray-800 rounded-lg p-8">
              {/* Inline Gap Input */}
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

              {/* Source */}
              {currentCard.sentence_source && (
                <div className="mt-6 text-xs text-gray-500">
                  Source: {currentCard.sentence_source}
                </div>
              )}

              {/* Audio Buttons (Manual playback) */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={handlePlayWordAudio}
                  className="px-4 py-2 bg-blue-900 text-blue-200 rounded hover:bg-blue-800 transition text-sm flex items-center gap-2"
                  disabled={isPlayingAudio}
                >
                  <span>🔊</span>
                  <span>Play Word</span>
                </button>
                <button
                  onClick={handlePlaySentenceAudio}
                  className="px-4 py-2 bg-purple-900 text-purple-200 rounded hover:bg-purple-800 transition text-sm flex items-center gap-2"
                  disabled={isPlayingAudio}
                >
                  <span>🔊</span>
                  <span>Play Sentence</span>
                </button>
              </div>
            </div>

            {/* Hint Panel */}
            <HintPanel
              correctAnswer={currentCard.correct_answer}
              wordTranslationPt={currentCard.word_translation_pt}
              sentenceTranslationPt={currentCard.sentence_translation_pt}
              hintLevel={hintLevel}
            />

            {/* Translations Panel (Always Visible) */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">🌐</span>
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                  Traduções
                </h3>
              </div>
              <div className="space-y-3">
                {/* Word Translation */}
                <div>
                  <div className="text-xs text-gray-400 mb-1">Palavra</div>
                  <div className="text-base text-gray-100">
                    {isTranslationAvailable(currentCard.word_translation_pt) ? (
                      currentCard.word_translation_pt
                    ) : (
                      <span className="text-gray-500 italic">Tradução indisponível</span>
                    )}
                  </div>
                </div>
                {/* Sentence Translation */}
                <div>
                  <div className="text-xs text-gray-400 mb-1">Frase</div>
                  <div className="text-base text-gray-100">
                    {isTranslationAvailable(currentCard.sentence_translation_pt) ? (
                      currentCard.sentence_translation_pt
                    ) : (
                      <span className="text-gray-500 italic">Tradução indisponível</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Feedback Message */}
            {feedback && (
              <div className={`bg-gray-800 rounded-lg p-6 ${
                feedback.correct ? 'border-l-4 border-green-500' : 'border-l-4 border-red-500'
              }`}>
                <div className="flex items-center gap-3">
                  {feedback.correct ? (
                    <>
                      <span className="text-3xl">✅</span>
                      <div>
                        <div className="text-green-400 font-semibold text-lg">Correct!</div>
                        {isPlayingAudio && (
                          <div className="text-gray-400 text-sm">Playing audio...</div>
                        )}
                      </div>
                    </>
                  ) : (
                    <>
                      <span className="text-3xl">❌</span>
                      <div>
                        <div className="text-red-400 font-semibold text-lg">Try again</div>
                        <div className="text-gray-400 text-sm">
                          Attempts: {attempts} • Hint level: {hintLevel}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-yellow-500">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">⚠️</span>
                  <div>
                    <div className="text-yellow-400 font-semibold text-lg">Error</div>
                    <div className="text-gray-400 text-sm">{errorMessage}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Audio Error Message (non-blocking) */}
            {audioError && (
              <div className="bg-gray-800 rounded-lg p-4 border-l-4 border-orange-500">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔇</span>
                  <div>
                    <div className="text-orange-400 font-semibold text-sm">Audio Error</div>
                    <div className="text-gray-400 text-xs">{audioError}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Debug Info (hidden in production) */}
            {import.meta.env.DEV && (
              <div className="bg-gray-800 rounded-lg p-4 text-xs text-gray-500">
                <p>correct_answer: <span className="text-gray-300">{currentCard.correct_answer}</span></p>
                <p>word: <span className="text-gray-300">{currentCard.word}</span></p>
                <p>hintLevel: <span className="text-gray-300">{hintLevel}</span></p>
                <p>attempts: <span className="text-gray-300">{attempts}</span></p>
                <p>isLocked: <span className="text-gray-300">{isInputLocked ? 'yes' : 'no'}</span></p>
                <p>isPlayingAudio: <span className="text-gray-300">{isPlayingAudio ? 'yes' : 'no'}</span></p>
              </div>
            )}
          </div>
        ) : (
          /* Loading State */
          <div className="text-center py-16">
            {errorMessage ? (
              <>
                {/* Error State */}
                <div className="text-red-400 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h8m-4 8h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-100 mb-2">
                  Failed to Load Card
                </h3>
                <p className="text-gray-400 mb-6 max-w-md mx-auto">
                  {errorMessage}
                </p>
                <button
                  onClick={() => {
                    handleRetryLoad();
                  }}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-semibold"
                >
                  🔄 Retry
                </button>
              </>
            ) : (
              <>
                {/* Loading State */}
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                <p className="text-gray-400">
                  Loading card...
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LingvistSession;
