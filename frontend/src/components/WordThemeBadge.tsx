/** Word Theme Badge Component */

import React, { useState, useEffect } from 'react';
import { insightsApi } from '../services/apiInsights';
import { withRetry } from '../utils/apiUtils';

interface WordThemeBadgeProps {
  wordId: string;
  className?: string;
}

const WordThemeBadge: React.FC<WordThemeBadgeProps> = ({ wordId, className = '' }) => {
  const [themes, setThemes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchThemes = async () => {
      if (!wordId) return;

      setLoading(true);
      try {
        const wordThemes = await withRetry(
          () => insightsApi.getWordThemes(wordId),
          { maxRetries: 1, baseDelay: 500 }
        );
        setThemes(wordThemes);
      } catch (err) {
        // Silently fail for themes - it's not critical
        console.warn('Could not fetch word themes:', err);
        setThemes([]);
      } finally {
        setLoading(false);
      }
    };

    fetchThemes();
  }, [wordId]);

  if (loading || themes.length === 0) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {themes.map((theme, index) => (
        <span
          key={index}
          className="status-pill min-h-7 border-violet-400/20 bg-violet-400/10 px-2.5 py-1 text-[11px] text-violet-200"
        >
          {theme}
        </span>
      ))}
    </div>
  );
};

export default WordThemeBadge;
