/** Feedback Message Component */

import React from 'react';
import InfoTooltip from './InfoTooltip';

interface FeedbackMessageProps {
  feedback?: {
    correct: boolean;
    correctAnswer: string;
    sentenceFull: string;
    quality: number;
    nextReview: string;
  };
  hint?: string;
  attempts?: number;
}

const FeedbackMessage: React.FC<FeedbackMessageProps> = ({
  feedback,
  hint,
  attempts = 1,
}) => {
  if (!feedback) return null;

  const { correct, correctAnswer, sentenceFull, quality, nextReview } = feedback;

  // Render correct feedback
  if (correct) {
    return (
      <div className="animate-fade-in">
        <div className="flex items-center gap-3 rounded-2xl border border-emerald-400/25 bg-emerald-400/10 p-4" data-testid="feedback">
          <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-emerald-400/15 text-emerald-200">✓</span>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-emerald-100">
              Muito bem — “{correctAnswer}” está correto.
            </h3>
            <p className="truncate text-xs text-emerald-100/75" title={sentenceFull}>{sentenceFull}</p>
          </div>
          <InfoTooltip label="Detalhes da resposta">
            Qualidade da lembrança: {quality}/5. Próxima revisão em {new Date(nextReview).toLocaleDateString('pt-BR')}.
          </InfoTooltip>
        </div>
      </div>
    );
  }

  // Render incorrect feedback with hints
  const getHintMessage = () => {
    if (attempts === 1) {
      return "Tente novamente";
    } else if (attempts === 2) {
      const firstLetter = correctAnswer[0];
      const blanks = "_".repeat(correctAnswer.length - 1);
      return `Primeira letra: ${firstLetter}${blanks}`;
    } else if (attempts === 3) {
      const halfLength = Math.ceil(correctAnswer.length / 2);
      const partial = correctAnswer.substring(0, halfLength);
      const blanks = "_".repeat(correctAnswer.length - halfLength);
      return `Parte da resposta: ${partial}${blanks}`;
    } else {
      return `A resposta é: ${correctAnswer}`;
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 rounded-2xl border border-red-400/25 bg-red-400/10 p-4" data-testid="feedback">
        <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-red-400/15 text-red-200">×</span>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-red-100">Ainda não</h3>
          <p className="text-xs text-red-100/75">{getHintMessage()}</p>
        </div>
        {hint && <InfoTooltip label="Ver dica">{hint}</InfoTooltip>}
      </div>
    </div>
  );
};

export default FeedbackMessage;
