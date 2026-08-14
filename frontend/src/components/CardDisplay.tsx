/** Card Display Component */

import React from 'react';
import type { CardResponse } from '../services/apiCards';
import GrammarBadge from './GrammarBadge';
import WordThemeBadge from './WordThemeBadge';
import InfoTooltip from './InfoTooltip';

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
      <div className="py-6 text-center text-2xl font-medium leading-relaxed tracking-[-0.02em] text-white sm:py-8 md:text-3xl" data-testid="card-sentence">
        <span>{beforeGap}</span>
        <span className="gap-highlight mx-1.5 inline-block min-w-[104px] rounded-lg border-b-2 border-primary-300 bg-primary-400/10 px-3 py-1 text-primary-200">
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
      <div className="flex gap-1.5" aria-label={`Memória: ${card.memory_stage}`}>
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
    <div className="w-full">
      <article className="surface-panel p-4 sm:p-5" data-testid="study-card">
        <header className="flex min-h-9 items-center justify-between gap-3 border-b border-white/[0.07] pb-3">
          <div className="flex items-center gap-3">
            {renderMemoryIndicator()}
            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-500">memória {card.memory_stage.toLowerCase()}</span>
          </div>
          {card.sentence_source && (
            <InfoTooltip label="Fonte da frase">
              <strong className="mb-1 block text-white">Fonte</strong>
              {card.sentence_source}
            </InfoTooltip>
          )}
        </header>

        {renderSentenceWithGap()}

        <div className="border-t border-white/[0.07] pt-3">
          <p className="truncate text-center text-sm italic text-gray-400" title={card.sentence_translation}>
            “{card.sentence_translation}”
          </p>
        </div>

        <footer className="mt-4 flex flex-wrap items-center gap-2">
          {card.grammar_hint && <GrammarBadge grammarHint={card.grammar_hint} />}
          <WordThemeBadge wordId={card.word_id} />
          <span className="flex-1" />
          <button
            onClick={onPlayWordAudio}
            disabled={loadingAudio}
            className="btn btn-secondary min-h-10 px-3 text-xs"
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
                Ouvir palavra
              </>
            )}
          </button>

          <button
            onClick={onPlaySentenceAudio}
            disabled={loadingAudio}
            className="btn btn-secondary min-h-10 px-3 text-xs"
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
                Ouvir frase
              </>
            )}
          </button>
        </footer>
      </article>
    </div>
  );
};

export default CardDisplay;
