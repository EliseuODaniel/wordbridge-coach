/** Answer Input Component */

import React, { useState, useRef, useEffect } from 'react';

interface AnswerInputProps {
  onSubmit: (answer: string) => void;
  isSubmitting?: boolean;
  placeholder?: string;
  feedback?: {
    correct: boolean;
    correctAnswer?: string;
  } | null;
  cardId?: string;  // Add cardId to detect card changes
}

const AnswerInput: React.FC<AnswerInputProps> = ({
  onSubmit,
  isSubmitting = false,
  placeholder = "Type your answer...",
  feedback = null,
  cardId,
}) => {
  const [answer, setAnswer] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Clear answer when card changes (new card = fresh start)
  useEffect(() => {
    if (cardId) {
      setAnswer('');
    }
  }, [cardId]);

  // Unified focus handling for feedback and card changes
  useEffect(() => {
    if (!inputRef.current) return;

    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;

      if (feedback) {
        if (feedback.correct) {
          setAnswer('');
          el.focus();
        } else {
          el.select();
          el.focus();
        }
      } else {
        // feedback null ou trocou card: só focar, sem select
        el.focus();
      }
    });
  }, [feedback, cardId]);  // Combined dependencies

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim() && !isSubmitting) {
      onSubmit(answer.trim());
      // Immediate focus after submission
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 0);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto">
      <div className="flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder={placeholder}
          disabled={isSubmitting}
          className="input flex-1 text-center text-lg"
          autoComplete="off"
          spellCheck={false}
          autoFocus
          data-testid="answer-input"
        />
        
        <button
          type="submit"
          disabled={!answer.trim() || isSubmitting}
          className="btn btn-primary px-6"
          data-testid="answer-submit"
        >
          {isSubmitting ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          ) : (
            'Check'
          )}
        </button>
      </div>
    </form>
  );
};

export default AnswerInput;
