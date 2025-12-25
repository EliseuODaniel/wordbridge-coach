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
    <div className="bg-gray-750 border border-gray-600 rounded-lg p-4 space-y-3">
      <div className="text-xs text-gray-400 font-semibold uppercase tracking-wide">
        Hints
      </div>

      {/* Level 1: Length Mask */}
      {showLengthMask && (
        <div className="flex items-start gap-2">
          <span className="text-yellow-400 text-sm">📏</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Length</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{lengthMask}</div>
          </div>
        </div>
      )}

      {/* Level 2: First Letter */}
      {showFirstLetter && (
        <div className="flex items-start gap-2">
          <span className="text-green-400 text-sm">🔤</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">First letter</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{firstLetterHint}</div>
          </div>
        </div>
      )}

      {/* Level 3: Reveal Letters */}
      {showRevealedLetters && (
        <div className="flex items-start gap-2">
          <span className="text-purple-400 text-sm">✨</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Reveal</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{revealedLetters}</div>
          </div>
        </div>
      )}

      {/* Level 4: Word Translation */}
      {showWordTranslation && (
        <div className="flex items-start gap-2">
          <span className="text-blue-400 text-sm">📝</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Word (PT)</div>
            <div className="text-sm text-gray-200">
              {wordTranslationPt || <span className="text-gray-500 italic">Tradução indisponível</span>}
            </div>
          </div>
        </div>
      )}

      {/* Level 5: Sentence Translation */}
      {showSentenceTranslation && (
        <div className="flex items-start gap-2">
          <span className="text-orange-400 text-sm">🌐</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Sentence (PT)</div>
            <div className="text-sm text-gray-200">
              {sentenceTranslationPt || <span className="text-gray-500 italic">Tradução indisponível</span>}
            </div>
          </div>
        </div>
      )}

      {/* Level 6: Complete Answer */}
      {showCompleteAnswer && (
        <div className="flex items-start gap-2">
          <span className="text-red-400 text-sm">💡</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Answer</div>
            <div className="text-sm font-mono font-bold text-gray-100 tracking-widest">
              {correctAnswer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HintPanel;
