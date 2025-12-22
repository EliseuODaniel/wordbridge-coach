/** Feedback Message Component */

import React from 'react';

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
      <div className="max-w-2xl mx-auto animate-fade-in">
        <div className="rounded-xl p-6 bg-green-900/70 border border-green-700 shadow-lg" data-testid="feedback">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">✅</span>
            <h3 className="text-lg font-semibold text-green-100">
              Excellent! "{correctAnswer}" is correct.
            </h3>
          </div>
          
          <div className="space-y-2 text-green-100">
            <p>
              <strong>Full sentence:</strong> {sentenceFull}
            </p>
            
            <div className="flex items-center gap-4 text-sm text-green-200">
              <span>
                <strong>Quality:</strong> {quality}/5
              </span>
              <span>
                <strong>Next review:</strong> {new Date(nextReview).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render incorrect feedback with hints
  const getHintMessage = () => {
    if (attempts === 1) {
      return "❌ Try again";
    } else if (attempts === 2) {
      const firstLetter = correctAnswer[0];
      const blanks = "_".repeat(correctAnswer.length - 1);
      return `❌ It's a noun. First letter: ${firstLetter}${blanks}`;
    } else if (attempts === 3) {
      const halfLength = Math.ceil(correctAnswer.length / 2);
      const partial = correctAnswer.substring(0, halfLength);
      const blanks = "_".repeat(correctAnswer.length - halfLength);
      return `❌ Something you read. Partial: ${partial}${blanks}`;
    } else {
      return `❌ The answer is: ${correctAnswer}`;
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <div className="rounded-xl p-6 bg-red-900/70 border border-red-700 shadow-lg" data-testid="feedback">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">❌</span>
          <h3 className="text-lg font-semibold text-red-100">
            Not quite right
          </h3>
        </div>
        
        <div className="text-red-100">
          <p className="mb-2">{getHintMessage()}</p>
          {hint && (
            <p className="text-sm text-yellow-100 bg-yellow-800 px-3 py-1 rounded-lg inline-block border border-yellow-700">
              💡 {hint}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedbackMessage;
