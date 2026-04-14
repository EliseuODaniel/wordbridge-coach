import { useCallback, useEffect, useRef, useState } from 'react';

import { cardsApi, type AnswerResponse, type CardResponse } from '../services/apiCards';
import { getApiErrorMessage, getApiErrorStatus } from '../services/apiErrors';
import { audioService } from '../services/audio';
import { statsService, type SettingsData, type StatsData } from '../services/stats';

interface UseStudySessionResult {
  attempts: number;
  currentCard: CardResponse | null;
  feedback: AnswerResponse | null;
  isSubmitting: boolean;
  loadingAudio: boolean;
  stats: StatsData | null;
  settings: SettingsData | null;
  refreshTrigger: number;
  handlePlaySentenceAudio: () => Promise<void>;
  handlePlayWordAudio: () => Promise<void>;
  handleSubmit: (answer: string) => Promise<void>;
}

export const useStudySession = (userId?: string): UseStudySessionResult => {
  const [currentCard, setCurrentCard] = useState<CardResponse | null>(null);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [stats, setStats] = useState<StatsData | null>(null);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [userHasInteracted, setUserHasInteracted] = useState(false);
  const nextCardTimeoutRef = useRef<number | null>(null);
  const retryLoadTimeoutRef = useRef<number | null>(null);
  const previousCardIdRef = useRef<string | null>(null);

  const clearPendingNextCardTimeout = useCallback(() => {
    if (nextCardTimeoutRef.current) {
      clearTimeout(nextCardTimeoutRef.current);
      nextCardTimeoutRef.current = null;
    }
  }, []);

  const clearPendingRetryTimeout = useCallback(() => {
    if (retryLoadTimeoutRef.current) {
      clearTimeout(retryLoadTimeoutRef.current);
      retryLoadTimeoutRef.current = null;
    }
  }, []);

  const playAudioUrl = useCallback(async (audioUrl?: string) => {
    if (!audioUrl) return;

    try {
      setLoadingAudio(true);
      await audioService.playFromUrl(audioUrl);
    } catch (error) {
      console.error('Error playing audio:', error);
    } finally {
      setLoadingAudio(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    if (!userId) {
      setStats(null);
      return;
    }

    try {
      const statsData = await statsService.getBasicStats(userId);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }, [userId]);

  const loadSettings = useCallback(async () => {
    if (!userId) {
      setSettings(null);
      return;
    }

    try {
      const settingsData = await statsService.getSettings(userId);
      setSettings(settingsData);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  }, [userId]);

  const loadNextCard = useCallback(async (excludeCardId?: string, retryCount = 0) => {
    const maxRetries = 3;
    const baseDelay = 1000;

    try {
      console.log('🔍 Loading next card...', { userId, excludeCardId, retryCount });
      console.log(`📝 User ID being used: ${userId}`);
      console.log(`📝 Exclude card ID: ${excludeCardId || 'none'}`);

      setCurrentCard(null);
      setIsSubmitting(true);
      setFeedback(null);
      setAttempts(0);
      setStartTime(Date.now());

      const card = await cardsApi.getNextCard(userId, excludeCardId);

      if (!card || !card.card_id || !card.sentence) {
        console.error('❌ Invalid card response:', {
          card,
          hasCardId: !!card?.card_id,
          hasSentence: !!card?.sentence,
        });
        throw new Error('Invalid card response: missing required fields');
      }

      console.log('✅ Card loaded successfully:', {
        cardId: `${card.card_id.slice(0, 8)}...`,
        wordId: `${card.word_id.slice(0, 8)}...`,
        sentenceLength: card.sentence.length,
      });
      setCurrentCard(card);
    } catch (error) {
      const errorStatus = getApiErrorStatus(error);
      const errorMessage = getApiErrorMessage(error, 'Failed to load next card');

      console.error(`❌ Error loading next card (attempt ${retryCount + 1}/${maxRetries + 1}):`, {
        error: errorMessage,
        status: errorStatus,
        userId,
        excludeCardId: excludeCardId || 'none',
      });

      if (retryCount < maxRetries) {
        const delay = baseDelay * Math.pow(2, retryCount);
        console.log(`🔄 Retrying card fetch in ${delay}ms... (attempt ${retryCount + 2}/${maxRetries + 1})`);

        clearPendingRetryTimeout();
        retryLoadTimeoutRef.current = window.setTimeout(() => {
          loadNextCard(excludeCardId, retryCount + 1);
          retryLoadTimeoutRef.current = null;
        }, delay);
        return;
      }

      console.error('❌ All retry attempts failed. Showing "No cards available".');
      setCurrentCard(null);
    } finally {
      setIsSubmitting(false);
    }
  }, [clearPendingRetryTimeout, userId]);

  const scheduleNextCardLoad = useCallback((cardId?: string) => {
    clearPendingNextCardTimeout();
    nextCardTimeoutRef.current = window.setTimeout(() => {
      loadNextCard(cardId);
      nextCardTimeoutRef.current = null;
    }, 1500);
  }, [clearPendingNextCardTimeout, loadNextCard]);

  const handleSubmit = useCallback(async (answer: string) => {
    if (!currentCard || isSubmitting) {
      console.log('❌ Cannot submit answer:', { hasCurrentCard: !!currentCard, isSubmitting });
      return;
    }

    console.log('🔝 Submitting answer:', {
      answer,
      cardId: `${currentCard.card_id.slice(0, 8)}...`,
      userId: userId?.slice(0, 8) ? `${userId.slice(0, 8)}...` : undefined,
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
      setAttempts((prev) => prev + 1);

      loadStats();

      console.log('[answer] correct=', response.correct, 'type=', typeof response.correct, 'strict check:', response.correct === true);
      console.log('✅ Answer submitted successfully:', {
        answer,
        correct: response.correct,
        quality: response.quality,
      });

      setRefreshTrigger((prev) => prev + 1);

      if (response.correct === true) {
        console.log('✅ Answer correct! Scheduling next card in 1500ms...');
        scheduleNextCardLoad(currentCard.card_id);
      } else {
        console.log('❌ Answer incorrect. User can try again with same card.');
        clearPendingNextCardTimeout();
      }
    } catch (error) {
      const status = getApiErrorStatus(error);
      const errorMessage = getApiErrorMessage(error, 'Error submitting answer');

      console.error('❌ Error submitting answer:', {
        error: errorMessage,
        status,
        rawError: error,
      });

      setFeedback({
        correct: false,
        correct_answer: status ? `Error ${status}: ${errorMessage}` : `Error: ${errorMessage}`,
        sentence_full: currentCard.sentence || '',
        quality: 0,
        next_review_at: new Date().toISOString(),
      });

      clearPendingNextCardTimeout();
    } finally {
      setIsSubmitting(false);
    }
  }, [clearPendingNextCardTimeout, currentCard, isSubmitting, loadStats, scheduleNextCardLoad, startTime, userId]);

  const handlePlayWordAudio = useCallback(async () => {
    await playAudioUrl(currentCard?.audio_word_url);
  }, [currentCard?.audio_word_url, playAudioUrl]);

  const handlePlaySentenceAudio = useCallback(async () => {
    await playAudioUrl(currentCard?.audio_sentence_url);
  }, [currentCard?.audio_sentence_url, playAudioUrl]);

  useEffect(() => {
    if (!currentCard?.card_id) {
      return;
    }

    const currentCardId = currentCard.card_id;
    const previousCardId = previousCardIdRef.current;
    previousCardIdRef.current = currentCardId;

    if (currentCard.audio_sentence_url && userHasInteracted && currentCardId !== previousCardId) {
      audioService.playFromUrl(currentCard.audio_sentence_url).catch((error) => {
        console.log('Auto-play sentence audio failed:', error);
      });
    }
  }, [currentCard?.audio_sentence_url, currentCard?.card_id, userHasInteracted]);

  useEffect(() => {
    loadNextCard();
    loadStats();
    loadSettings();

    const handleUserInteraction = () => {
      setUserHasInteracted(true);
    };

    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('keydown', handleUserInteraction, { once: true });
    document.addEventListener('touchstart', handleUserInteraction, { once: true });

    return () => {
      audioService.clearCache();
      clearPendingNextCardTimeout();
      clearPendingRetryTimeout();
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };
  }, [clearPendingNextCardTimeout, clearPendingRetryTimeout, loadNextCard, loadSettings, loadStats]);

  return {
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
  };
};
