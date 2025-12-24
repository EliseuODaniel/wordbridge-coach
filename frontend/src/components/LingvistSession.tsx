/** Lingvist Mode Study Session Component */

import React, { useState, useEffect, useCallback } from 'react';
import { cardsApi, type LingvistCardResponse, type AnswerResponse } from '../services/api';
import InlineGapInput from './InlineGapInput';
import HintPanel from './HintPanel';
import AudioAfterCorrect from './AudioAfterCorrect';

interface LingvistSessionProps {
  userId?: string;
  onExit?: () => void;
}

const LingvistSession: React.FC<LingvistSessionProps> = ({ userId, onExit }) => {
  // State management
  const [currentCard, setCurrentCard] = useState<LingvistCardResponse | null>(null);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [hintLevel, setHintLevel] = useState(0); // 0-5 based on mistakes
  const [isInputLocked, setIsInputLocked] = useState(false);

  // Track if audio is playing after correct
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Load next card
  const loadNextCard = useCallback(async (excludeCardId?: string) => {
    try {
      console.log('🔍 Loading Lingvist card...', { userId, excludeCardId });

      // Clear state for new card
      setCurrentCard(null);
      setFeedback(null);
      setAttempts(0);
      setHintLevel(0);
      setIsInputLocked(false);
      setIsPlayingAudio(false);
      setStartTime(Date.now());

      const card = await cardsApi.getNextLingvistCard(userId, excludeCardId);

      // Validate card
      if (!card || !card.card_id || !card.sentence) {
        console.error('❌ Invalid Lingvist card response:', card);
        throw new Error('Invalid card response');
      }

      console.log('✅ Lingvist card loaded:', {
        word: card.word,
        is_new: card.is_new,
        micro_progress: card.micro_progress,
        correct_answer: card.correct_answer
      });

      setCurrentCard(card);

    } catch (error) {
      console.error('❌ Error loading Lingvist card:', error);
      setCurrentCard(null);
    }
  }, [userId]);

  // Handle answer submission
  const handleSubmit = useCallback(async (answer: string) => {
    if (!currentCard || isSubmitting || isInputLocked) {
      return;
    }

    console.log('🔝 Submitting answer:', {
      answer,
      correct_answer: currentCard.correct_answer
    });

    try {
      setIsSubmitting(true);
      const responseTime = Date.now() - startTime;

      const response = await cardsApi.submitAnswer(
        currentCard.card_id,
        {
          answer,
          response_time_ms: responseTime,
        },
        userId
      );

      setFeedback(response);
      const newAttemptCount = attempts + 1;
      setAttempts(newAttemptCount);

      console.log('✅ Answer submitted:', {
        answer,
        correct: response.correct,
        quality: response.quality,
        attempt: newAttemptCount
      });

      if (response.correct === true) {
        // CORRECT ANSWER
        console.log('✅ Correct! Locking input and playing audio...');

        // Lock input immediately
        setIsInputLocked(true);

        // Play audio and advance after it finishes (via AudioAfterCorrect component)
        setIsPlayingAudio(true);

      } else {
        // INCORRECT ANSWER - increase hint level, don't advance
        console.log('❌ Incorrect! Showing more hints...');

        // Increase hint level based on attempts (max 5)
        const newHintLevel = Math.min(newAttemptCount, 5);
        setHintLevel(newHintLevel);

        // Stay on same card - user can try again with more hints
      }

    } catch (error) {
      console.error('❌ Error submitting answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [currentCard, isSubmitting, isInputLocked, attempts, startTime, userId]);

  // Initialize session
  useEffect(() => {
    loadNextCard();
  }, [loadNextCard]);

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
            <a
              href="/?mode=spec4"
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition text-sm"
            >
              Switch to Spec4 🎯
            </a>
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
            <div className="flex gap-2 flex-wrap">
              {currentCard.grammar_tag_pt !== 'UNK' && (
                <span className="px-3 py-1 bg-blue-900 text-blue-200 text-sm rounded">
                  {currentCard.grammar_tag_pt}
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
                sentence={currentCard.sentence}
                gap={currentCard.gap}
                correctAnswer={currentCard.correct_answer}
                onSubmit={handleSubmit}
                disabled={isSubmitting || isPlayingAudio}
                isCorrect={feedback?.correct === true}
              />

              {/* Source */}
              {currentCard.sentence_source && (
                <div className="mt-6 text-xs text-gray-500">
                  Source: {currentCard.sentence_source}
                </div>
              )}
            </div>

            {/* Hint Panel */}
            <HintPanel
              grammarTagPt={currentCard.grammar_tag_pt}
              correctAnswer={currentCard.correct_answer}
              wordTranslationPt={currentCard.word_translation_pt}
              sentenceTranslationPt={currentCard.sentence_translation_pt}
              hintLevel={hintLevel}
            />

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

            {/* Debug Info (hidden in production) */}
            {import.meta.env.DEV && (
              <div className="bg-gray-800 rounded-lg p-4 text-xs text-gray-500">
                <p>correct_answer: <span className="text-gray-300">{currentCard.correct_answer}</span></p>
                <p>word: <span className="text-gray-300">{currentCard.word}</span></p>
                <p>hintLevel: <span className="text-gray-300">{hintLevel}</span></p>
                <p>attempts: <span className="text-gray-300">{attempts}</span></p>
                <p>isLocked: <span className="text-gray-300">{isInputLocked ? 'yes' : 'no'}</span></p>
              </div>
            )}
          </div>
        ) : (
          /* Loading State */
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-400">
              Loading card...
            </p>
          </div>
        )}

        {/* Audio After Correct (invisible component) */}
        {feedback?.correct === true && currentCard && isPlayingAudio && (
          <AudioAfterCorrect
            audioSentenceUrl={currentCard.audio_sentence_url}
            onFinished={() => {
              console.log('🔄 Audio finished, loading next card...');
              setIsPlayingAudio(false);
              loadNextCard(currentCard.card_id);
            }}
            timeoutMs={3000}
          />
        )}
      </div>
    </div>
  );
};

export default LingvistSession;
