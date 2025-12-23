/** Progress Over Time Chart Component */

import React, { useState, useEffect } from 'react';
import { insightsApi, type DailyStatsResponse } from '../services/api';
import { withRetry } from '../utils/apiUtils';

interface ProgressOverTimeChartProps {
  userId: string;
  refreshTrigger?: number;
  className?: string;
}

const ProgressOverTimeChart: React.FC<ProgressOverTimeChartProps> = ({ userId, refreshTrigger, className = '' }) => {
  const [data, setData] = useState<DailyStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDailyStats = async () => {
      setLoading(true);
      setError(null);

      try {
        const dailyStats = await withRetry(
          () => insightsApi.getUserDailyStats(userId, 30),
          {
            maxRetries: 2,
            baseDelay: 1000,
            retryCondition: (error) => {
              if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
                return true;
              }
              if (error.response?.status >= 500) {
                return true;
              }
              return false;
            }
          }
        );
        setData(dailyStats);
      } catch (err) {
        console.error('Error fetching daily stats after retries:', err);
        // Check if it's a 404 (no data) vs actual error
        if ((err as any)?.response?.status === 404) {
          setError('No progress data yet');
        } else if ((err as any)?.response?.status >= 500) {
          setError('Server temporarily unavailable - please refresh');
        } else if ((err as any)?.code === 'NETWORK_ERROR') {
          setError('Network error - check your connection');
        } else {
          setError('Failed to load progress data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDailyStats();
  }, [userId, refreshTrigger]);

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
          <div className="h-32 bg-gray-700 rounded mb-3"></div>
          <div className="h-3 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Progress Over Time</h3>
        <div className="text-gray-500 text-sm">
          {error || 'No progress data available'}
        </div>
      </div>
    );
  }

  const { daily_stats, summary } = data;

  if (daily_stats.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Progress Over Time</h3>
        <div className="text-gray-500 text-sm">
          No daily progress data yet. Keep studying to see your learning trends!
        </div>
      </div>
    );
  }

  // Find max values for scaling
  const maxMasteredWords = Math.max(...daily_stats.map(d => d.cumulative_mastered_words));

  // Generate chart paths
  const generateVocabularyPath = () => {
    return daily_stats
      .map((stat, index) => {
        const x = 40 + (index / (daily_stats.length - 1)) * 220;
        const y = 110 - (stat.cumulative_mastered_words / maxMasteredWords) * 80;
        return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
      })
      .join(' ');
  };

  const generateAccuracyPath = () => {
    return daily_stats
      .map((stat, index) => {
        const x = 40 + (index / (daily_stats.length - 1)) * 220;
        const y = 110 - (stat.accuracy * 80);
        return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
      })
      .join(' ');
  };

  const vocabularyPath = generateVocabularyPath();
  const accuracyPath = generateAccuracyPath();

  return (
    <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
      <h3 className="text-sm font-medium text-gray-300 mb-3">Progress Over Time</h3>

      {/* Dual-axis chart */}
      <div className="mb-3 h-32">
        <svg width="100%" height="128" viewBox="0 0 300 128" className="text-xs">
          {/* Grid lines */}
          {[0, 20, 40, 60, 80, 100].map((pct, i) => (
            <line
              key={i}
              x1="40"
              y1={110 - (pct * 0.8)}
              x2="260"
              y2={110 - (pct * 0.8)}
              stroke="#374151"
              strokeWidth="1"
            />
          ))}

          {/* Vocabulary growth line */}
          <path
            d={vocabularyPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
          />

          {/* Accuracy line */}
          <path
            d={accuracyPath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="4,2"
          />

          {/* Data points for vocabulary */}
          {daily_stats.map((stat, index) => {
            const x = 40 + (index / (daily_stats.length - 1)) * 220;
            const y = 110 - (stat.cumulative_mastered_words / maxMasteredWords) * 80;
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="2"
                fill="#10b981"
              />
            );
          })}

          {/* Data points for accuracy */}
          {daily_stats.map((stat, index) => {
            const x = 40 + (index / (daily_stats.length - 1)) * 220;
            const y = 110 - (stat.accuracy * 80);
            return (
              <circle
                key={`acc-${index}`}
                cx={x}
                cy={y}
                r="2"
                fill="#3b82f6"
              />
            );
          })}

          {/* Y-axis labels */}
          <text x="35" y="115" textAnchor="end" fill="#9ca3af" fontSize="10">0</text>
          <text x="35" y="65" textAnchor="end" fill="#9ca3af" fontSize="10">50</text>
          <text x="35" y="25" textAnchor="end" fill="#9ca3af" fontSize="10">100</text>
          <text x="35" y="15" textAnchor="end" fill="#10b981" fontSize="9">Words</text>
          <text x="35" y="125" textAnchor="end" fill="#3b82f6" fontSize="9">Accuracy%</text>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-4 text-xs text-gray-400 mb-3">
        <span className="flex items-center">
          <span className="w-3 h-0.5 bg-green-500 mr-1"></span>
          Vocabulary
        </span>
        <span className="flex items-center">
          <span className="w-3 h-0.5 bg-blue-500 border-dashed mr-1"></span>
          Accuracy
        </span>
      </div>

      {/* Summary statistics */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-gray-400">Total Vocabulary</div>
          <div className="text-lg font-semibold text-gray-200">
            {summary.vocabulary_growth.toLocaleString()} words
          </div>
        </div>
        <div>
          <div className="text-gray-400">Avg Daily Accuracy</div>
          <div className="text-lg font-semibold text-gray-200">
            {(summary.avg_accuracy * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-gray-400">Avg Daily Cards</div>
          <div className="text-lg font-semibold text-gray-200">
            {summary.avg_daily_cards.toFixed(1)}
          </div>
        </div>
        <div>
          <div className="text-gray-400">Active Days</div>
          <div className="text-lg font-semibold text-gray-200">
            {summary.total_days}
          </div>
        </div>
      </div>

      {/* Progress indicator */}
      <div className="mt-3 pt-3 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Learning Progress</span>
          <span>{summary.total_new_words} new words mastered</span>
        </div>
        <div className="mt-1 w-full bg-gray-700 rounded-full h-1.5">
          <div
            className="bg-green-500 h-1.5 rounded-full"
            style={{
              width: `${Math.min(100, (summary.vocabulary_growth / 100) * 100)}%`
            }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default ProgressOverTimeChart;