/** Lingvist Mode Study Session Component */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cardsApi, type LingvistCardResponse, type AnswerResponse } from '../services/api';
import { audioService } from '../services/audio';

interface LingvistSessionProps {
  userId?: string;
  onExit?: () => void;
}

const LingvistSession: React.FC<LingvistSessionProps> = ({ userId, onExit }) => {
  // State management
  const [currentCard, setCurrentCard] = useState<LingvistCardResponse | null>(null);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());

  // Ref to manage next card timeout
  const nextCardTimeoutRef = useRef<number | null>(null);

  // Track if user has interacted (for autoplay gating)
  const [userHasInteracted, setUserHasInteracted] = useState(false);

  // Ref to track previous card_id for autoplay logic
  const previousCardIdRef = useRef<string | null>(null);

  // Load next card
  const loadNextCard = useCallback(async (excludeCardId?: string) => {
    try {
      console.log('🔍 Loading Lingvist card...', { userId, excludeCardId });

      // Clear current card immediately to show loading state
      setCurrentCard(null);
      setIsSubmitting(true);
      setFeedback(null);
      setAttempts(0);
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
        micro_progress: card.micro_progress
      });

      setCurrentCard(card);

    } catch (error) {
      console.error('❌ Error loading Lingvist card:', error);
      setCurrentCard(null);
    } finally {
      setIsSubmitting(false);
    }
  }, [userId]);

  // Handle answer submission (will be enhanced in PASSO 5)
  const handleSubmit = async (answer: string) => {
    if (!currentCard || isSubmitting) {
      return;
    }

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
      setAttempts(attempts + 1);

      console.log('✅ Answer submitted:', {
        answer,
        correct: response.correct,
        quality: response.quality
      });

      // Play audio after correct answer (Lingvist mode requirement)
      // TODO: PASSO 5 will implement audio-after-correct flow

      // Load next card if answer was correct
      if (response.correct === true) {
        if (nextCardTimeoutRef.current) {
          clearTimeout(nextCardTimeoutRef.current);
        }
        nextCardTimeoutRef.current = window.setTimeout(() => {
          loadNextCard(currentCard?.card_id);
          nextCardTimeoutRef.current = null;
        }, 1500);
      }

    } catch (error) {
      console.error('❌ Error submitting answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Initialize session
  useEffect(() => {
    loadNextCard();

    // Detect first user interaction
    const handleUserInteraction = () => {
      if (!userHasInteracted) {
        setUserHasInteracted(true);
      }
    };

    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('keydown', handleUserInteraction, { once: true });
    document.addEventListener('touchstart', handleUserInteraction, { once: true });

    return () => {
      audioService.clearCache();
      if (nextCardTimeoutRef.current) {
        clearTimeout(nextCardTimeoutRef.current);
      }
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };
  }, [loadNextCard]);

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-gray-100 mb-2">
            Lingvist Mode
          </h1>
          <p className="text-gray-500 text-sm">
            Cloze deletion with progressive hints
          </p>
        </div>

        {/* Exit Button */}
        <div className="flex justify-end mb-4">
          <button
            onClick={onExit}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition"
          >
            ← Exit
          </button>
        </div>

        {/* Main Content */}
        {currentCard ? (
          <div className="space-y-8">
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

            {/* Card Display */}
            <div className="bg-gray-800 rounded-lg p-8">
              {/* Grammar Tag (hide if UNK) */}
              {currentCard.grammar_tag_pt !== 'UNK' && (
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-900 text-blue-200 text-sm rounded">
                    {currentCard.grammar_tag_pt}
                  </span>
                  {currentCard.is_new && (
                    <span className="ml-2 inline-block px-3 py-1 bg-green-900 text-green-200 text-sm rounded">
                      New
                    </span>
                  )}
                </div>
              )}

              {/* Sentence with Gap */}
              <div className="mb-6">
                <p className="text-xl text-gray-100 leading-relaxed">
                  {currentCard.sentence}
                </p>
              </div>

              {/* Bottom Sheet - Translations */}
              {(currentCard.word_translation_pt || currentCard.sentence_translation_pt) && (
                <div className="mt-6 pt-6 border-t border-gray-700">
                  {currentCard.word_translation_pt && (
                    <p className="text-gray-400 mb-2">
                      <span className="font-semibold text-gray-300">Word:</span> {currentCard.word_translation_pt}
                    </p>
                  )}
                  {currentCard.sentence_translation_pt && (
                    <p className="text-gray-400">
                      <span className="font-semibold text-gray-300">Sentence:</span> {currentCard.sentence_translation_pt}
                    </p>
                  )}
                </div>
              )}

              {/* Source */}
              {currentCard.sentence_source && (
                <div className="mt-4 text-xs text-gray-500">
                  Source: {currentCard.sentence_source}
                </div>
              )}

              {/* Audio Buttons (temporary - will be inline in PASSO 5) */}
              <div className="mt-6 flex gap-4">
                <button
                  onClick={() => audioService.playFromUrl(currentCard.audio_word_url)}
                  disabled={loadingAudio}
                  className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition"
                >
                  🔊 Word
                </button>
                <button
                  onClick={() => audioService.playFromUrl(currentCard.audio_sentence_url)}
                  disabled={loadingAudio}
                  className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition"
                >
                  🔊 Sentence
                </button>
              </div>
            </div>

            {/* Debug Info */}
            <div className="bg-gray-800 rounded-lg p-4 text-xs text-gray-500">
              <p>correct_answer: <span className="text-gray-300">{currentCard.correct_answer}</span></p>
              <p>word: <span className="text-gray-300">{currentCard.word}</span></p>
            </div>
          </div>
        ) : (
          /* Loading State */
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-400">
              {isSubmitting ? 'Loading card...' : 'No cards available'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LingvistSession;
