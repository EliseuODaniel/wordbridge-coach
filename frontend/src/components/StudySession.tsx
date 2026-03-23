/** Main Study Session Component */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cardsApi, getApiErrorMessage, getApiErrorStatus } from '../services/api';
import type { CardResponse, AnswerResponse } from '../services/api';
import { audioService } from '../services/audio';
import { statsService, type StatsData, type SettingsData } from '../services/stats';
import CardDisplay from './CardDisplay';
import AnswerInput from './AnswerInput';
import FeedbackMessage from './FeedbackMessage';
import SessionCounter from './SessionCounter';
import InsightsSection from './InsightsSection';

interface StudySessionProps {
  userId?: string;
}

const StudySession: React.FC<StudySessionProps> = ({ userId }) => {
  // State management
  const [currentCard, setCurrentCard] = useState<CardResponse | null>(null);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [stats, setStats] = useState<StatsData | null>(null);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Track if user has interacted (for autoplay gating)
  const [userHasInteracted, setUserHasInteracted] = useState(false);

  // Ref to manage next card timeout and prevent "ghost timers"
  const nextCardTimeoutRef = useRef<number | null>(null);

  // Ref to track previous card_id for autoplay logic
  const previousCardIdRef = useRef<string | null>(null);

  // Load stats from API
  const loadStats = useCallback(async () => {
    try {
      const statsData = await statsService.getBasicStats(userId);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }, [userId]);

  // Load settings from API
  const loadSettings = useCallback(async () => {
    try {
      const settingsData = await statsService.getSettings(userId);
      setSettings(settingsData);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  }, [userId]);

  // Load next card with robust retry mechanism
  const loadNextCard = useCallback(async (excludeCardId?: string, retryCount = 0) => {
    const maxRetries = 3;
    const baseDelay = 1000; // 1 second

    try {
      console.log(`🔍 Loading next card...`, { userId, excludeCardId, retryCount });
      console.log(`📝 User ID being used: ${userId}`);
      console.log(`📝 Exclude card ID: ${excludeCardId || 'none'}`);

      // Clear current card immediately to show loading spinner
      // This prevents "visual repetition" of the old card
      setCurrentCard(null);
      setIsSubmitting(true);
      setFeedback(null);
      setAttempts(0);
      setStartTime(Date.now());

      const card = await cardsApi.getNextCard(userId, excludeCardId);

      // Validate card has required fields
      if (!card || !card.card_id || !card.sentence) {
        console.error('❌ Invalid card response:', { card, hasCardId: !!card?.card_id, hasSentence: !!card?.sentence });
        throw new Error('Invalid card response: missing required fields');
      }

      console.log('✅ Card loaded successfully:', {
        cardId: card.card_id.slice(0, 8) + '...',
        wordId: card.word_id.slice(0, 8) + '...',
        sentenceLength: card.sentence.length
      });
      setCurrentCard(card);

    } catch (error) {
      const errorStatus = getApiErrorStatus(error);
      const errorMessage = getApiErrorMessage(error, 'Failed to load next card');

      console.error(`❌ Error loading next card (attempt ${retryCount + 1}/${maxRetries + 1}):`, {
        error: errorMessage,
        status: errorStatus,
        userId: userId,
        excludeCardId: excludeCardId || 'none'
      });

      // Retry logic with exponential backoff
      if (retryCount < maxRetries) {
        const delay = baseDelay * Math.pow(2, retryCount); // 1s, 2s, 4s
        console.log(`🔄 Retrying card fetch in ${delay}ms... (attempt ${retryCount + 2}/${maxRetries + 1})`);

        setTimeout(() => {
          loadNextCard(excludeCardId, retryCount + 1);
        }, delay);
        return;
      }

      // If all retries failed, set card to null and show appropriate message
      console.error('❌ All retry attempts failed. Showing "No cards available".');
      setCurrentCard(null);
    } finally {
      setIsSubmitting(false);
    }
  }, [userId]);

  // Handle answer submission
  const handleSubmit = async (answer: string) => {
    if (!currentCard || isSubmitting) {
      console.log('❌ Cannot submit answer:', { hasCurrentCard: !!currentCard, isSubmitting });
      return;
    }

    console.log('🔝 Submitting answer:', {
      answer,
      cardId: currentCard.card_id.slice(0, 8) + '...',
      userId: userId?.slice(0, 8) + '...'
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
      setAttempts(attempts + 1);

      // Refresh stats after answer
      loadStats();

      // Log response.correct type and value for diagnosis
      console.log('[answer] correct=', response.correct, 'type=', typeof response.correct, 'strict check:', response.correct === true);

      console.log('✅ Answer submitted successfully:', {
        answer,
        correct: response.correct,
        quality: response.quality
      });

      // Trigger insights refresh
      setRefreshTrigger(prev => prev + 1);

      // Clear any existing timeout before scheduling a new one
      if (nextCardTimeoutRef.current) {
        console.log('[timeout] Clearing previous timeout:', nextCardTimeoutRef.current);
        clearTimeout(nextCardTimeoutRef.current);
        nextCardTimeoutRef.current = null;
      }

      // Load next card ONLY if answer was correct (STRICT BOOL CHECK)
      // If incorrect, user stays on same card to try again
      if (response.correct === true) {
        console.log('✅ Answer correct! Scheduling next card in 1500ms...');
        nextCardTimeoutRef.current = window.setTimeout(() => {
          console.log('[timeout] Executing loadNextCard');
          loadNextCard(currentCard?.card_id);
          nextCardTimeoutRef.current = null; // Clear after execution
        }, 1500); // Slightly longer delay to show feedback
      } else {
        console.log('❌ Answer incorrect. User can try again with same card.');
        // Explicitly ensure no timeout is scheduled for incorrect answers
        nextCardTimeoutRef.current = null;
      }

    } catch (error) {
      const status = getApiErrorStatus(error);
      const errorMessage = getApiErrorMessage(error, 'Error submitting answer');

      console.error('❌ Error submitting answer:', {
        error: errorMessage,
        status,
        rawError: error
      });

      // Show user feedback but still allow them to try again
      setFeedback({
        correct: false,
        correct_answer: status ? `Error ${status}: ${errorMessage}` : `Error: ${errorMessage}`,
        sentence_full: currentCard.sentence || '',
        quality: 0,
        next_review_at: new Date().toISOString()
      });

      // Clear any timeout on error to prevent "ghost timers"
      if (nextCardTimeoutRef.current) {
        console.log('[error] Clearing timeout due to error');
        clearTimeout(nextCardTimeoutRef.current);
        nextCardTimeoutRef.current = null;
      }

    } finally {
      setIsSubmitting(false);
    }
  };

  // Play audio for word
  const handlePlayWordAudio = async () => {
    if (!currentCard || !currentCard.audio_word_url) return;

    try {
      setLoadingAudio(true);

      // Play audio directly from backend URL
      await audioService.playFromUrl(currentCard.audio_word_url);

    } catch (error) {
      console.error('Error playing word audio:', error);
    } finally {
      setLoadingAudio(false);
    }
  };

  // Play audio for sentence
  const handlePlaySentenceAudio = async () => {
    if (!currentCard || !currentCard.audio_sentence_url) return;

    try {
      setLoadingAudio(true);

      // Play audio directly from backend URL
      await audioService.playFromUrl(currentCard.audio_sentence_url);

    } catch (error) {
      console.error('Error playing sentence audio:', error);
    } finally {
      setLoadingAudio(false);
    }
  };


  // Auto-play sentence audio when card changes (only after user interaction)
  useEffect(() => {
    if (!currentCard?.card_id) {
      return; // No card yet
    }

    const currentCardId = currentCard.card_id;
    const previousCardId = previousCardIdRef.current;

    // Update ref for next comparison
    previousCardIdRef.current = currentCardId;

    // Only auto-play if:
    // 1. User has interacted (prevents autoplay blocking)
    // 2. card_id actually changed (ignores userHasInteracted becoming true)
    if (currentCard?.audio_sentence_url && userHasInteracted && currentCardId !== previousCardId) {
      audioService.playFromUrl(currentCard.audio_sentence_url).catch(error => {
        console.log('Auto-play sentence audio failed:', error);
      });
    }
  }, [currentCard?.card_id, currentCard?.audio_sentence_url, userHasInteracted]);

  // Initialize session
  useEffect(() => {
    loadNextCard();
    loadStats(); // Load initial stats
    loadSettings(); // Load initial settings

    // Detect first user interaction (click, keydown, touch)
    const handleUserInteraction = () => {
      setUserHasInteracted(true);
    };

    // Add event listeners for user interaction
    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('keydown', handleUserInteraction, { once: true });
    document.addEventListener('touchstart', handleUserInteraction, { once: true });

    return () => {
      // Cleanup audio on unmount
      audioService.clearCache();
      // Cleanup any pending timeout to prevent "ghost timers"
      if (nextCardTimeoutRef.current) {
        console.log('[unmount] Clearing pending timeout');
        clearTimeout(nextCardTimeoutRef.current);
        nextCardTimeoutRef.current = null;
      }
      // Remove event listeners
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };
  }, [loadNextCard, loadStats, loadSettings]);

  
return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="container mx-auto px-4" data-testid="study-container">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="text-center flex-1">
            <h1 className="text-4xl font-extrabold text-gray-100 mb-2">
              FillTheWord
            </h1>
            <p className="text-gray-500 text-sm">
              Spec4 Mode • Multiple Choice Training
            </p>
          </div>
          <div className="flex gap-2">
            <a
              href="/?mode=lingvist"
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition text-sm"
            >
              Switch to Lingvist ✍️
            </a>
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
