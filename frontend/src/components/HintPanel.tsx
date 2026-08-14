/** Hint Panel for Lingvist Mode - Progressive hints */

import React from 'react';

interface HintPanelProps {
  correctAnswer: string;
  wordTranslationPt?: string | null;
  sentenceTranslationPt?: string | null;
  hintLevel: number; // 0-6 based on mistakes/time
  showAll?: boolean; // For debugging
}

const HintPanel: React.FC<HintPanelProps> = ({
  correctAnswer,
  wordTranslationPt,
  sentenceTranslationPt,
  hintLevel,
  showAll = false,
}) => {
  // Hide if "UNK" or level 0 (no hints yet)
  if (!showAll && hintLevel === 0) {
    return null;
  }

  const shouldShow = (level: number) => showAll || hintLevel >= level;

  // NEW HINT PROGRESSION: One new visible hint per mistake (up to level 6)

  // Level 1: Length Mask (ALWAYS show at level 1, independent of grammar)
  const lengthMask = correctAnswer.split('').map(() => '_').join(' ');
  const showLengthMask = shouldShow(1);

  // Level 2: First Letter
  const firstLetterHint = correctAnswer[0] + ' ' + correctAnswer.slice(1).split('').map(() => '_').join(' ');
  const showFirstLetter = shouldShow(2);

  // Level 3-5: Reveal Letters (progressive reveal up to ~80%)
  const maxReveal = Math.ceil(correctAnswer.length * 0.8); // Cap at 80%
  let revealCount = 0;
  if (hintLevel === 3) revealCount = Math.min(2, correctAnswer.length);
  else if (hintLevel === 4) revealCount = Math.min(4, correctAnswer.length);
  else if (hintLevel === 5) revealCount = Math.min(6, maxReveal);
  else if (hintLevel >= 6) revealCount = maxReveal;

  const revealedLetters = correctAnswer
    .split('')
    .map((char, idx) => (idx < revealCount ? char : '_'))
    .join(' ');
  const showRevealedLetters = shouldShow(3);

  // Level 4: Word Translation (or "Tradução indisponível")
  const showWordTranslation = shouldShow(4);

  // Level 5: Sentence Translation (or "Tradução indisponível")
  const showSentenceTranslation = shouldShow(5);

  // Level 6: Complete Answer (final hint)
  const showCompleteAnswer = shouldShow(6);

  if (!showLengthMask && !showFirstLetter && !showRevealedLetters && !showWordTranslation && !showSentenceTranslation && !showCompleteAnswer) {
    return null;
  }

  return (
    <section className="surface-soft p-3">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-500">
        Pistas
      </div>
      <div className="flex flex-wrap gap-2">

      {/* Level 1: Length Mask */}
      {showLengthMask && (
        <div className="rounded-xl border border-amber-400/15 bg-amber-400/[0.06] px-3 py-2">
          <div className="text-[10px] text-amber-200/70">Tamanho</div>
          <div className="font-mono text-xs tracking-widest text-gray-200">{lengthMask}</div>
        </div>
      )}

      {/* Level 2: First Letter */}
      {showFirstLetter && (
        <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.06] px-3 py-2">
          <div className="text-[10px] text-emerald-200/70">Primeira letra</div>
          <div className="font-mono text-xs tracking-widest text-gray-200">{firstLetterHint}</div>
        </div>
      )}

      {/* Level 3: Reveal Letters */}
      {showRevealedLetters && (
        <div className="rounded-xl border border-violet-400/15 bg-violet-400/[0.06] px-3 py-2">
          <div className="text-[10px] text-violet-200/70">Revelação</div>
          <div className="font-mono text-xs tracking-widest text-gray-200">{revealedLetters}</div>
        </div>
      )}

      {/* Level 4: Word Translation */}
      {showWordTranslation && (
        <div className="max-w-48 rounded-xl border border-cyan-400/15 bg-cyan-400/[0.06] px-3 py-2">
          <div className="text-[10px] text-cyan-200/70">Palavra em PT</div>
          <div className="truncate text-xs text-gray-200">{wordTranslationPt || <span className="italic text-gray-500">Indisponível</span>}</div>
        </div>
      )}

      {/* Level 5: Sentence Translation */}
      {showSentenceTranslation && (
        <div className="max-w-72 rounded-xl border border-orange-400/15 bg-orange-400/[0.06] px-3 py-2">
          <div className="text-[10px] text-orange-200/70">Frase em PT</div>
          <div className="truncate text-xs text-gray-200">{sentenceTranslationPt || <span className="italic text-gray-500">Indisponível</span>}</div>
        </div>
      )}

      {/* Level 6: Complete Answer */}
      {showCompleteAnswer && (
        <div className="rounded-xl border border-red-400/20 bg-red-400/[0.07] px-3 py-2">
          <div className="text-[10px] text-red-200/70">Resposta</div>
          <div className="font-mono text-xs font-bold tracking-widest text-gray-100">{correctAnswer}</div>
        </div>
      )}
      </div>
    </section>
  );
};

export default HintPanel;
