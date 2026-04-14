import { useCallback, useEffect, useState } from 'react';

import { cardsApi, type LingvistCardResponse, type AnswerResponse } from '../services/apiCards';
import { getApiErrorMessage, getApiErrorStatus } from '../services/apiErrors';
import { audioService } from '../services/audio';
import { normalizeLingvistText } from './lingvistSessionHelpers';

interface UseLingvistSessionResult {
  attempts: number;
  audioError: string | null;
  currentCard: LingvistCardResponse | null;
  errorMessage: string | null;
  feedback: AnswerResponse | null;
  hintLevel: number;
  isInputLocked: boolean;
  isPlayingAudio: boolean;
  isSubmitting: boolean;
  handlePlaySentenceAudio: () => Promise<void>;
  handlePlayWordAudio: () => Promise<void>;
  handleRetryLoad: () => Promise<void>;
  handleSubmit: (answer: string) => Promise<void>;
  handleUserEdit: () => void;
}

export const useLingvistSession = (userId?: string): UseLingvistSessionResult => {
  const [currentCard, setCurrentCard] = useState<LingvistCardResponse | null>(null);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [hintLevel, setHintLevel] = useState(0);
  const [isInputLocked, setIsInputLocked] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  const resetRoundState = useCallback(() => {
    setCurrentCard(null);
    setFeedback(null);
    setErrorMessage(null);
    setAttempts(0);
    setHintLevel(0);
    setIsInputLocked(false);
    setIsPlayingAudio(false);
    setAudioError(null);
    setStartTime(Date.now());
  }, []);

  const preloadCardAudio = useCallback((card: LingvistCardResponse) => {
    if (card.audio_word_url) {
      audioService.preloadFromUrl(card.audio_word_url).catch((error) => {
        console.warn('Failed to preload word audio:', error);
      });
    }

    if (card.audio_sentence_url) {
      audioService.preloadFromUrl(card.audio_sentence_url).catch((error) => {
        console.warn('Failed to preload sentence audio:', error);
      });
    }
  }, []);

  const playAudioUrl = useCallback(
    async (
      audioUrl: string | undefined,
      unavailableMessage: string,
      failedMessage: string
    ) => {
      if (!audioUrl) {
        setAudioError(unavailableMessage);
        return;
      }

      setAudioError(null);

      try {
        await audioService.playFromUrl(audioUrl);
      } catch (error) {
        console.error(failedMessage, error);
        setAudioError(failedMessage);
      }
    },
    []
  );

  const loadNextCard = useCallback(async (excludeCardId?: string) => {
    try {
      console.log('🔍 Loading Lingvist card...', { userId, excludeCardId });

      resetRoundState();

      const card = await cardsApi.getNextLingvistCard(userId, excludeCardId);

      if (!card || !card.card_id || !card.sentence) {
        console.error('❌ Invalid Lingvist card response:', card);
        throw new Error('Invalid card response');
      }

      console.log('✅ Lingvist card loaded:', {
        word: card.word,
        is_new: card.is_new,
        micro_progress: card.micro_progress,
        correct_answer: card.correct_answer,
      });

      setCurrentCard(card);
      preloadCardAudio(card);
    } catch (error) {
      console.error('❌ Error loading Lingvist card:', error);

      const status = getApiErrorStatus(error);
      const message = getApiErrorMessage(error, 'Failed to load card. Please try again.');

      setErrorMessage(status ? `Error ${status}: ${message}` : message);
      setCurrentCard(null);
    }
  }, [preloadCardAudio, resetRoundState, userId]);

  const handleUserEdit = useCallback(() => {
    setFeedback(null);
    setErrorMessage(null);
  }, []);

  const handlePlayWordAudio = useCallback(async () => {
    await playAudioUrl(
      currentCard?.audio_word_url,
      'Word audio not available',
      'Failed to play word audio'
    );
  }, [currentCard?.audio_word_url, playAudioUrl]);

  const handlePlaySentenceAudio = useCallback(async () => {
    await playAudioUrl(
      currentCard?.audio_sentence_url,
      'Sentence audio not available',
      'Failed to play sentence audio'
    );
  }, [currentCard?.audio_sentence_url, playAudioUrl]);

  const handleSubmit = useCallback(async (answer: string) => {
    if (!currentCard || isSubmitting || isInputLocked) {
      return;
    }

    console.log('🔝 Submitting answer:', {
      answer,
      correct_answer: currentCard.correct_answer,
    });

    const isCorrectLocal =
      normalizeLingvistText(answer) === normalizeLingvistText(currentCard.correct_answer);
    console.log('🎯 Local validation:', { isCorrectLocal, answer, correct: currentCard.correct_answer });

    let audioPromise: Promise<void> | null = null;
    if (isCorrectLocal && currentCard.audio_sentence_url) {
      console.log('🔊 Starting audio playback...');
      setIsInputLocked(true);
      setIsPlayingAudio(true);

      audioPromise = audioService.playFromUrlAndWaitEnded(currentCard.audio_sentence_url)
        .then(() => {
          console.log('✅ Audio finished (full playback)');
        })
        .catch((error) => {
          console.error('❌ Audio error:', error);
        });
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
      const newAttemptCount = attempts + 1;
      setAttempts(newAttemptCount);

      console.log('✅ Answer submitted:', {
        answer,
        correct: response.correct,
        quality: response.quality,
        attempt: newAttemptCount,
      });

      if (isCorrectLocal) {
        if (audioPromise) {
          await audioPromise;
        }

        await loadNextCard(currentCard.card_id);
      } else {
        const maxHintLevel = 6;
        setHintLevel(Math.min(newAttemptCount, maxHintLevel));
      }
    } catch (error) {
      console.error('❌ Error submitting answer:', error);
      setErrorMessage('Failed to submit answer. Please try again.');

      if (audioPromise) {
        await audioPromise;
      }
    } finally {
      setIsSubmitting(false);
      if (!isCorrectLocal) {
        setIsPlayingAudio(false);
      }
    }
  }, [attempts, currentCard, isInputLocked, isSubmitting, loadNextCard, startTime, userId]);

  useEffect(() => {
    loadNextCard();
  }, [loadNextCard]);

  return {
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
    handleRetryLoad: async () => {
      setErrorMessage(null);
      await loadNextCard();
    },
    handleSubmit,
    handleUserEdit,
  };
};
