/** Hint Panel for Lingvist Mode - Progressive hints */

import React from 'react';

interface HintPanelProps {
  grammarTagPt: string;
  correctAnswer: string;
  wordTranslationPt?: string | null;
  sentenceTranslationPt?: string | null;
  hintLevel: number; // 0-5 based on mistakes/time
  showAll?: boolean; // For debugging
}

const HintPanel: React.FC<HintPanelProps> = ({
  grammarTagPt,
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

  // Level 1: Grammar Tag (already shown in card, but we reinforce here)
  const showGrammarTag = shouldShow(1) && grammarTagPt !== 'UNK';

  // Level 2: Length Mask (ex: "_ _ _" for 3 letters)
  const lengthMask = correctAnswer.split('').map(() => '_').join(' ');
  const showLengthMask = shouldShow(2);

  // Level 3: First Letter (ex: "b _ _ k")
  const firstLetterHint = correctAnswer[0] + ' ' + correctAnswer.slice(1).split('').map(() => '_').join(' ');
  const showFirstLetter = shouldShow(3);

  // Level 4: Reveal Letters (progressive based on level)
  const revealCount = Math.max(1, hintLevel - 3); // Level 4: 1 letter, Level 5: 2 letters, etc.
  const revealedLetters = correctAnswer
    .split('')
    .map((char, idx) => (idx < revealCount ? char : '_'))
    .join(' ');
  const showRevealedLetters = shouldShow(4);

  // Level 5: Translation (PT-BR)
  const showTranslation = shouldShow(5) && (wordTranslationPt || sentenceTranslationPt);

  if (!showGrammarTag && !showLengthMask && !showFirstLetter && !showRevealedLetters && !showTranslation) {
    return null;
  }

  return (
    <div className="bg-gray-750 border border-gray-600 rounded-lg p-4 space-y-3">
      <div className="text-xs text-gray-400 font-semibold uppercase tracking-wide">
        Hints
      </div>

      {/* Level 1: Grammar Tag */}
      {showGrammarTag && (
        <div className="flex items-start gap-2">
          <span className="text-blue-400 text-sm">📝</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Grammar</div>
            <div className="text-sm text-gray-200">{grammarTagPt}</div>
          </div>
        </div>
      )}

      {/* Level 2: Length Mask */}
      {showLengthMask && (
        <div className="flex items-start gap-2">
          <span className="text-yellow-400 text-sm">📏</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Length</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{lengthMask}</div>
          </div>
        </div>
      )}

      {/* Level 3: First Letter */}
      {showFirstLetter && (
        <div className="flex items-start gap-2">
          <span className="text-green-400 text-sm">🔤</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">First letter</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{firstLetterHint}</div>
          </div>
        </div>
      )}

      {/* Level 4: Reveal Letters */}
      {showRevealedLetters && (
        <div className="flex items-start gap-2">
          <span className="text-purple-400 text-sm">✨</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Reveal</div>
            <div className="text-sm font-mono text-gray-200 tracking-widest">{revealedLetters}</div>
          </div>
        </div>
      )}

      {/* Level 5: Translation */}
      {showTranslation && (
        <div className="flex items-start gap-2">
          <span className="text-orange-400 text-sm">🌐</span>
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">Translation</div>
            {wordTranslationPt && (
              <div className="text-sm text-gray-200">
                <span className="font-semibold">Word:</span> {wordTranslationPt}
              </div>
            )}
            {sentenceTranslationPt && (
              <div className="text-sm text-gray-200 mt-1">
                <span className="font-semibold">Sentence:</span> {sentenceTranslationPt}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default HintPanel;
