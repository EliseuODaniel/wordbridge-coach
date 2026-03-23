/** Audio After Correct - Play sentence audio and wait before advancing */

import React, { useEffect, useRef } from 'react';
import { audioService } from '../services/audio';

interface AudioAfterCorrectProps {
  audioSentenceUrl: string;
  onFinished: () => void; // Callback to load next card
  timeoutMs?: number; // Default 3000ms
}

const AudioAfterCorrect: React.FC<AudioAfterCorrectProps> = ({
  audioSentenceUrl,
  onFinished,
  timeoutMs = 3000,
}) => {
  const hasFinishedRef = useRef(false);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    let isMounted = true;
    hasFinishedRef.current = false;

    const playAudioAndWait = async () => {
      try {
        console.log('🔊 Playing sentence audio after correct...');

        // Play audio and wait for it to finish
        await audioService.playFromUrl(audioSentenceUrl);

        if (isMounted) {
          console.log('✅ Audio finished');
          hasFinishedRef.current = true;

          // Load next card immediately after audio ends
          onFinished();
        }
      } catch (error) {
        console.error('❌ Error playing audio:', error);

        if (isMounted) {
          hasFinishedRef.current = true;

          // Even on error, load next card after timeout
          timeoutRef.current = window.setTimeout(() => {
            onFinished();
          }, 1000);
        }
      }
    };

    // Start audio playback
    playAudioAndWait();

    // Backup timeout: if audio takes too long or doesn't play
    timeoutRef.current = window.setTimeout(() => {
      if (isMounted && !hasFinishedRef.current) {
        console.log('⏱️ Audio timeout, advancing to next card');
        hasFinishedRef.current = true;
        onFinished();
      }
    }, timeoutMs);

    return () => {
      isMounted = false;

      // Cleanup timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Stop audio if unmounting
      audioService.clearCache();
    };
  }, [audioSentenceUrl, onFinished, timeoutMs]);

  // Don't render anything visible - this is a logic component
  return null;
};

export default AudioAfterCorrect;
