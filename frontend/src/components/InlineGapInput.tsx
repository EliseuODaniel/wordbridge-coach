/** Inline Gap Input for Lingvist Mode */

import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';

interface InlineGapInputProps {
  sentence: string;
  gap: { start: number; end: number };
  correctAnswer: string;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onUserEdit?: () => void;
}

const InlineGapInput: React.FC<InlineGapInputProps> = ({
  sentence,
  gap,
  correctAnswer,
  onSubmit,
  disabled = false,
  isCorrect = false,
  isIncorrect = false,
  onUserEdit,
}) => {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const submitPendingRef = useRef(false);

  // Normalize text for comparison (case-insensitive, trim, no extra spaces)
  const normalizeText = (text: string) => {
    return text.toLowerCase().trim().replace(/\s+/g, ' ');
  };

  // Focus input on mount
  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  // Clear pending submission lock after the parent finishes processing.
  useEffect(() => {
    if (!disabled && !isCorrect) {
      submitPendingRef.current = false;
      inputRef.current?.focus();
      if (isIncorrect) {
        inputRef.current?.select();
      }
    }
  }, [disabled, isCorrect, isIncorrect]);

  // Split sentence into parts: before gap, gap (input), after gap
  const beforeGap = sentence.slice(0, gap.start);
  const afterGap = sentence.slice(gap.end);

  // Auto-submit when answer matches exactly
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (submitPendingRef.current || disabled) return;

    const newValue = e.target.value;

    // If editing after incorrect answer, clear feedback
    if (isIncorrect && newValue !== value) {
      onUserEdit?.();
    }

    setValue(newValue);

    // Auto-submit on exact match (normalized)
    if (normalizeText(newValue) === normalizeText(correctAnswer)) {
      console.log('✅ Auto-submit: exact match', {
        typed: newValue,
        correct: correctAnswer,
      });
      submitPendingRef.current = true;
      onSubmit(newValue);
    }
  };

  // Handle Enter key as fallback
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !submitPendingRef.current && !disabled && value.trim()) {
      e.preventDefault();
      console.log('⏎ Enter fallback: submitting answer', value);
      submitPendingRef.current = true;
      onSubmit(value);
    }
  };

  return (
    <div className="flex flex-wrap items-baseline gap-1 text-xl text-gray-100 leading-relaxed">
      {/* Text before gap */}
      <span>{beforeGap}</span>

      {/* Inline input */}
      <input
        ref={inputRef}
        data-testid="lingvist-inline-input"
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={`
          inline-block px-2 py-1 mx-1 rounded border-b-2 bg-transparent
          text-center font-semibold transition-all duration-200
          focus:outline-none focus:ring-0
          ${
            disabled
              ? isCorrect
                ? 'border-green-500 text-green-400'
                : isIncorrect
                  ? 'border-red-500 text-red-400'
                  : 'border-gray-500 text-gray-100'
              : 'border-gray-500 text-gray-100 focus:border-primary-500'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        style={{
          minWidth: `${Math.max(correctAnswer.length * 0.6, 3)}em`,
          maxWidth: '15em',
        }}
        autoComplete="off"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
      />

      {/* Text after gap */}
      <span>{afterGap}</span>
    </div>
  );
};

export default InlineGapInput;
