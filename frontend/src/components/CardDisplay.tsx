/** Card Display Component */

import React from 'react';
import type { CardResponse } from '../services/api';

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
      <div className="text-2xl md:text-3xl font-medium text-center mb-6">
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

      {/* Sentence with Gap */}
      {renderSentenceWithGap()}

      {/* Translation and Grammar Hint */}
      <div className="space-y-3 mb-6">
        <div className="text-center">
          <span className="text-gray-400 italic">
            "{card.sentence_translation}"
          </span>
        </div>
        
        <div className="text-center">
          <span className="text-sm text-yellow-600 bg-yellow-900 px-3 py-1 rounded-full">
            💡 {card.grammar_hint}
          </span>
        </div>
      </div>

      {/* Audio Controls */}
      <div className="flex justify-center gap-4">
        <button
          onClick={onPlayWordAudio}
          disabled={loadingAudio}
          className="btn btn-secondary flex items-center gap-2"
          title="Play word pronunciation"
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
          className="btn btn-secondary flex items-center gap-2"
          title="Play full sentence"
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
  );
};

export default CardDisplay;
