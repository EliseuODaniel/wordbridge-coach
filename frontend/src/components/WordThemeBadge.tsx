/** Word Theme Badge Component */

import React, { useState, useEffect } from 'react';
import { insightsApi } from '../services/api';
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
          {
            maxRetries: 1,
            baseDelay: 500,
            retryCondition: (error) => {
              if (error.response?.status >= 500) {
                return true;
              }
              return false;
            }
          }
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
          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900/50 text-purple-200 border border-purple-700/50"
        >
          {theme}
        </span>
      ))}
    </div>
  );
};

export default WordThemeBadge;