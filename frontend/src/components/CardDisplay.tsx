/** Card Display Component */

import React from 'react';
import type { CardResponse } from '../services/api';
import GrammarBadge from './GrammarBadge';
import WordThemeBadge from './WordThemeBadge';

interface CardDisplayProps {
  card: CardResponse;
  onPlayWordAudio: () => void;
  onPlaySentenceAudio: () => void;
  loadingAudio?: boolean;
}

const CardDisplay: React.FC<CardDisplayProps> = ({
  card,
  onPlayWordAudio,
  onPlaySentenceAudio,
  loadingAudio = false,
}) => {
  // Render sentence with gap
  const renderSentenceWithGap = () => {
    const { sentence, gap } = card;
    const beforeGap = sentence.substring(0, gap.start);
    const afterGap = sentence.substring(gap.end);
    
    return (
      <div className="text-2xl md:text-3xl font-medium text-center mb-6" data-testid="card-sentence">
        <span>{beforeGap}</span>
        <span className="inline-block min-w-[120px] mx-2 px-4 py-2 border-b-4 border-blue-500 bg-blue-900 rounded-t-lg gap-highlight">
          ___
        </span>
        <span>{afterGap}</span>
      </div>
    );
  };

  // Render memory indicator (bolinhas)
  const renderMemoryIndicator = () => {
    const stageMapping: Record<string, number> = {
      'new': 0,
      'learning': 1,
      'relearn': 1,
      'review': 3,
      'mature': 4,
      // Uppercase variants (Spec4 SM-2 values)
      'NEW': 0,
      'LEARNING': 1,
      'RELEARN': 1,
      'REVIEW': 3,
      'MATURE': 4,
    };

    const filledDots = stageMapping[card.memory_stage] || 0;
    const totalDots = 4;

    return (
      <div className="flex justify-center gap-2 mb-4">
        {Array.from({ length: totalDots }).map((_, index) => {
          const isFilled = index < filledDots;
          let dotClass = 'memory-dot memory-dot-empty';
          
          if (isFilled) {
            if (filledDots <= 1) {
              dotClass = 'memory-dot memory-dot-learning';
            } else if (filledDots <= 2) {
              dotClass = 'memory-dot memory-dot-learning';
            } else if (filledDots === 3) {
              dotClass = 'memory-dot memory-dot-review';
            } else {
              dotClass = 'memory-dot memory-dot-mature';
            }
          }

          return (
            <div
              key={index}
              className={dotClass}
              title={`Memory stage: ${card.memory_stage} (${filledDots}/4)`}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Memory Indicator */}
      {renderMemoryIndicator()}

      {/* Card container with improved styling */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg mb-6" data-testid="study-card">
        {/* Sentence with Gap */}
        {renderSentenceWithGap()}

        {/* Grammar Badge above translation */}
        <div className="text-center mb-3">
          <GrammarBadge grammarHint={card.grammar_hint} />
        </div>

        {/* Word Theme Badge */}
        <div className="text-center mb-3">
          <WordThemeBadge wordId={card.word_id} />
        </div>

        {/* Sentence Source Badge */}
        {card.sentence_source && (
          <div className="text-center mb-3">
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-amber-900/30 border border-amber-700/50 rounded-full text-amber-300 text-xs font-medium">
              📚 {card.sentence_source}
            </span>
          </div>
        )}

        {/* Translation */}
        <div className="text-center">
          <span className="text-gray-400 italic text-sm">
            "{card.sentence_translation}"
          </span>
        </div>

        {/* Audio Controls */}
        <div className="flex justify-center gap-4 mt-4">
          <button
            onClick={onPlayWordAudio}
            disabled={loadingAudio}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-gray-200 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Play word pronunciation"
            data-testid="audio-word-button"
            aria-label="Play word pronunciation"
          >
            {loadingAudio ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                Loading...
              </>
            ) : (
              <>
                🔊 Word
              </>
            )}
          </button>

          <button
            onClick={onPlaySentenceAudio}
            disabled={loadingAudio}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-gray-200 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Play full sentence"
            data-testid="audio-sentence-button"
            aria-label="Play sentence pronunciation"
          >
            {loadingAudio ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                Loading...
              </>
            ) : (
              <>
                🔉 Sentence
              </>
            )}
          </button>
        </div>
      </div>

          </div>
  );
};

export default CardDisplay;
