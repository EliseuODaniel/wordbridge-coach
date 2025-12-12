/** Main Study Session Component */

import React, { useState, useEffect, useCallback } from 'react';
import { cardsApi } from '../services/api';
import type { CardResponse, AnswerResponse } from '../services/api';
import { audioService } from '../services/audio';
import { statsService, type StatsData, type SettingsData } from '../services/stats';
import CardDisplay from './CardDisplay';
import AnswerInput from './AnswerInput';
import FeedbackMessage from './FeedbackMessage';
import SessionCounter from './SessionCounter';

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

  // Load next card
  const loadNextCard = useCallback(async () => {
    try {
      setIsSubmitting(true);
      setFeedback(null);
      setAttempts(0);
      setStartTime(Date.now());

      const card = await cardsApi.getNextCard(userId);

      setCurrentCard(card);

    } catch (error) {
      console.error('❌ Error loading next card:', error);
      console.error('❌ Error response:', (error as any)?.response?.data);
      console.error('❌ Error status:', (error as any)?.response?.status);
      setCurrentCard(null);
    } finally {
      setIsSubmitting(false);
    }
  }, [userId]);

  // Handle answer submission
  const handleSubmit = async (answer: string) => {
    if (!currentCard || isSubmitting) return;

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

      console.log('Answer submitted:', { answer, response });

      // If correct, load next card after delay
      if (response.correct) {
        setTimeout(() => {
          loadNextCard();
        }, 2000);
      }
      
    } catch (error) {
      console.error('Error submitting answer:', error);
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

  
  
  // Initialize session
  useEffect(() => {
    loadNextCard();
    loadStats(); // Load initial stats
    loadSettings(); // Load initial settings

    return () => {
      // Cleanup audio on unmount
      audioService.clearCache();
    };
  }, [loadNextCard, loadStats, loadSettings]);

  
return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">
            FillTheWord
          </h1>
          <p className="text-gray-400">
            Learn vocabulary with smart spaced repetition
          </p>
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
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                placeholder="Type the missing word..."
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
              {isSubmitting ? 'Loading your next card...' : 'No cards available'}
            </p>
          </div>
        )}

        {/* Keyboard Shortcuts Help */}
        <div className="text-center mt-12 text-sm text-gray-400">
          <p>Press <kbd className="px-2 py-1 bg-gray-700 text-gray-100 rounded">Enter</kbd> to submit answer</p>
        </div>
      </div>
    </div>
  );
};

export default StudySession;
