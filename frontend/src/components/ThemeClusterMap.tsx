/** Theme Cluster Map Component */

import React, { useState, useEffect } from 'react';
import { insightsApi, type ThemePerformanceResponse } from '../services/apiInsights';
import { getApiErrorCode, getApiErrorMessage, getApiErrorStatus } from '../services/apiErrors';
import { withRetry } from '../utils/apiUtils';

interface ThemeClusterMapProps {
  userId: string;
  refreshTrigger?: number;
  className?: string;
}

const ThemeClusterMap: React.FC<ThemeClusterMapProps> = ({ userId, refreshTrigger, className = '' }) => {
  const [themes, setThemes] = useState<ThemePerformanceResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchThemes = async () => {
      setLoading(true);
      setError(null);

      try {
        const themesData = await withRetry(
          () => insightsApi.getUserThemes(userId),
          { maxRetries: 2, baseDelay: 1000 }
        );
        setThemes(themesData);
      } catch (err) {
        console.error('Error fetching theme performance after retries:', err);
        const status = getApiErrorStatus(err);
        const code = getApiErrorCode(err);
        const message = getApiErrorMessage(err, 'Unknown error');

        if (status === 404) {
          setError('No theme data available yet');
        } else if (typeof status === 'number' && status >= 500) {
          setError('Server temporarily unavailable - please refresh');
        } else if (code === 'NETWORK_ERROR' || message.includes('Network Error')) {
          setError('Network error - check your connection');
        } else {
          setError(`Error: ${message}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchThemes();
  }, [userId, refreshTrigger]);

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-12 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Performance by Theme</h3>
        <div className="text-gray-500 text-sm">
          {error}
        </div>
      </div>
    );
  }

  if (themes.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Performance by Theme</h3>
        <div className="text-gray-500 text-sm">
          No theme data available yet. Keep practicing to see your performance by word themes!
        </div>
      </div>
    );
  }

  // Sort themes by accuracy (worst first) for better visibility
  const sortedThemes = [...themes].sort((a, b) => a.accuracy - b.accuracy);

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.8) return 'bg-green-500';
    if (accuracy >= 0.6) return 'bg-yellow-500';
    if (accuracy >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  
  return (
    <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
      <h3 className="text-sm font-medium text-gray-300 mb-3">Performance by Theme</h3>

      {/* Simple list-based visualization */}
      <div className="space-y-2">
        {sortedThemes.map((theme) => (
          <div key={theme.theme_id} className="flex items-center space-x-3">
            {/* Theme name */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 truncate">
                {theme.name}
              </div>
              <div className="text-xs text-gray-400">
                {theme.attempts} attempts • {Math.round(theme.avg_response_time_ms / 1000)}s avg
              </div>
            </div>

            {/* Accuracy indicator */}
            <div className="flex items-center space-x-2">
              <div className="text-sm font-medium text-gray-300">
                {(theme.accuracy * 100).toFixed(0)}%
              </div>
              <div className={`w-12 h-2 rounded-full ${getAccuracyColor(theme.accuracy)}`}>
                <div
                  className={`h-2 rounded-full ${getAccuracyColor(theme.accuracy)}`}
                  style={{ width: `${theme.accuracy * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Performance:</span>
          <div className="flex items-center space-x-2">
            <span className="flex items-center">
              <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
              Poor
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
              Fair
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              Good
            </span>
          </div>
        </div>
      </div>

      {/* Difficulty words hint */}
      {themes.some(t => t.difficulty_words.length > 0) && (
        <div className="mt-2 text-xs text-gray-500">
          Themes with larger circles and red colors indicate areas where you struggle most.
        </div>
      )}
    </div>
  );
};

export default ThemeClusterMap;
