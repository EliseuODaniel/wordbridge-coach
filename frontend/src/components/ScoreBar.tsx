/**
 * ScoreBar Component
 *
 * Displays a quality score (0-100) with color coding.
 */

import React from 'react';

interface ScoreBarProps {
  score: number; // 0-100
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const ScoreBar: React.FC<ScoreBarProps> = ({
  score,
  size = 'md',
  showLabel = true,
  className = ''
}) => {
  const displayedScore = Math.max(0, Math.min(100, score));

  // Color coding based on score
  const getColor = (s: number): string => {
    if (s >= 80) return 'bg-green-500';
    if (s >= 60) return 'bg-yellow-500';
    if (s >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getTextColor = (s: number): string => {
    if (s >= 80) return 'text-green-400';
    if (s >= 60) return 'text-yellow-400';
    if (s >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const sizeClasses = {
    sm: { bar: 'h-1.5', text: 'text-xs' },
    md: { bar: 'h-2.5', text: 'text-sm' },
    lg: { bar: 'h-4', text: 'text-base' }
  };

  const percentage = displayedScore;
  const colorClass = getColor(displayedScore);
  const textColorClass = getTextColor(displayedScore);
  const { bar: barSize, text: textSize } = sizeClasses[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Bar container */}
      <div className={`flex-1 bg-gray-700 rounded-full overflow-hidden ${barSize}`}>
        <div
          className={`h-full ${colorClass} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Score label */}
      {showLabel && (
        <span className={`${textColorClass} ${textSize} font-semibold tabular-nums min-w-[3rem] text-right`}>
          {Math.round(displayedScore)}
        </span>
      )}
    </div>
  );
};

export default ScoreBar;
