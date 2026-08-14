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

  // Unified focus handling for feedback and card changes
  useEffect(() => {
    if (!inputRef.current) return;

    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;

      if (feedback) {
        if (!feedback.correct) {
          el.select();
        }
      }

      el.focus();
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
    <form onSubmit={handleSubmit} className="mx-auto max-w-xl">
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder={placeholder}
          disabled={isSubmitting}
          className="input min-w-0 flex-1 text-center text-base font-medium sm:text-lg"
          autoComplete="off"
          spellCheck={false}
          autoFocus
          data-testid="answer-input"
        />
        
        <button
          type="submit"
          disabled={!answer.trim() || isSubmitting}
          className="btn btn-primary shrink-0 px-5"
          data-testid="answer-submit"
        >
          {isSubmitting ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          ) : (
            'Conferir'
          )}
        </button>
      </div>
    </form>
  );
};

export default AnswerInput;
