/** Modal for replaying previous card (read-only, no answer submission) */

import React, { useEffect } from 'react';
import { audioService } from '../services/audio';

interface PreviousCardReplayModalProps {
  open: boolean;
  onClose: () => void;
  title: string | null;          // sentence with gap (e.g., "The ___ was here.")
  answer: string | null;         // correct answer (word or correct_answer)
  translation: string | null;    // sentence translation
  source: string | null;         // source title if exists
  audioWordUrl: string | null;   // URL for word audio
  audioSentenceUrl: string | null; // URL for sentence audio
  autoPlay?: boolean;            // Auto-play sentence on open (default: false)
}

const PreviousCardReplayModal: React.FC<PreviousCardReplayModalProps> = ({
  open,
  onClose,
  title,
  answer,
  translation,
  source,
  audioWordUrl,
  audioSentenceUrl,
  autoPlay = false,
}) => {
  // Auto-play sentence audio when modal opens (if enabled)
  useEffect(() => {
    if (open && autoPlay && audioSentenceUrl) {
      // Small delay to ensure modal is rendered
      const timer = setTimeout(() => {
        audioService.playFromUrl(audioSentenceUrl);
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [open, autoPlay, audioSentenceUrl]);

  const handlePlayWord = () => {
    if (audioWordUrl) {
      audioService.playFromUrl(audioWordUrl);
    }
  };

  const handlePlaySentence = () => {
    if (audioSentenceUrl) {
      audioService.playFromUrl(audioSentenceUrl);
    }
  };

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Frase Anterior
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Badge: Read-only */}
          <div className="mb-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              Apenas Visualização
            </span>
          </div>

          {/* Content */}
          <div className="space-y-4">
            {/* Sentence with gap */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-lg font-medium text-gray-900 dark:text-white leading-relaxed">
                {title || 'Frase não disponível'}
              </p>
            </div>

            {/* Answer */}
            {answer && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border-l-4 border-green-500">
                <p className="text-sm font-semibold text-green-800 dark:text-green-200 mb-1">
                  Resposta:
                </p>
                <p className="text-xl font-bold text-green-900 dark:text-green-100">
                  {answer}
                </p>
              </div>
            )}

            {/* Source */}
            {source && (
              <div className="text-sm text-gray-600 dark:text-gray-400 italic">
                <span className="font-medium">Source:</span> {source}
              </div>
            )}

            {/* Translation */}
            {translation && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-medium">Tradução:</span> {translation}
              </div>
            )}

            {/* Audio Buttons */}
            <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={handlePlayWord}
                disabled={!audioWordUrl}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
                Play Word
              </button>
              <button
                onClick={handlePlaySentence}
                disabled={!audioSentenceUrl}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-secondary-600 text-white rounded-lg hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
                Play Sentence
              </button>
            </div>

            {/* Close Button */}
            <div className="pt-4">
              <button
                onClick={onClose}
                className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors font-medium"
              >
                Voltar para o card atual
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviousCardReplayModal;
