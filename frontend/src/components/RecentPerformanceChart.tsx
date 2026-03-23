/** Recent Performance Chart Component */

import React, { useState, useEffect } from 'react';
import {
  insightsApi,
  getApiErrorCode,
  getApiErrorStatus,
  type RecentPerformanceResponse,
} from '../services/api';
import { withRetry } from '../utils/apiUtils';

interface RecentPerformanceChartProps {
  userId: string;
  className?: string;
  refreshTrigger?: number;
}

const RecentPerformanceChart: React.FC<RecentPerformanceChartProps> = ({ userId, className = '', refreshTrigger }) => {
  const [data, setData] = useState<RecentPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      setLoading(true);
      setError(null);

      try {
        const performanceData = await withRetry(
          () => insightsApi.getRecentPerformance(userId),
          { maxRetries: 2, baseDelay: 1000 }
        );
        setData(performanceData);
      } catch (err) {
        console.error('Error fetching recent performance after retries:', err);
        const status = getApiErrorStatus(err);
        const code = getApiErrorCode(err);

        if (status === 404) {
          setError('No performance data yet');
        } else if (typeof status === 'number' && status >= 500) {
          setError('Server temporarily unavailable - please refresh');
        } else if (code === 'NETWORK_ERROR') {
          setError('Network error - check your connection');
        } else {
          setError('Failed to load performance data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPerformance();
  }, [userId, refreshTrigger]);

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
          <div className="h-24 bg-gray-700 rounded mb-3"></div>
          <div className="h-3 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Recent Performance</h3>
        <div className="text-gray-500 text-sm">
          {error || 'No performance data available'}
        </div>
      </div>
    );
  }

  const { metrics, recent_responses } = data;

  // Calculate moving average accuracy for sparkline
  const calculateMovingAverage = (responses: boolean[], windowSize: number = 5) => {
    const averages = [];
    for (let i = 0; i < responses.length; i++) {
      const start = Math.max(0, i - windowSize + 1);
      const end = i + 1;
      const window = responses.slice(start, end);
      const avg = window.reduce((sum, val) => sum + (val ? 1 : 0), 0) / window.length;
      averages.push(avg);
    }
    return averages;
  };

  const movingAverages = calculateMovingAverage(recent_responses.map(r => r.was_correct));
  const maxAvg = Math.max(...movingAverages, 1);

  // Generate sparkline path
  const generateSparklinePath = () => {
    if (movingAverages.length === 0) return '';

    const width = 280;
    const height = 80;
    const padding = 10;

    return movingAverages
      .map((avg, index) => {
        const x = padding + (index / (movingAverages.length - 1)) * (width - 2 * padding);
        const y = height - padding - (avg / maxAvg) * (height - 2 * padding);
        return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
      })
      .join(' ');
  };

  const sparklinePath = generateSparklinePath();

  return (
    <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
      <h3 className="text-sm font-medium text-gray-300 mb-3">Recent Performance</h3>

      {/* Sparkline Chart */}
      <div className="mb-3 h-20 flex items-center justify-center">
        <svg width="100%" height="80" viewBox="0 0 300 80" className="text-xs">
          {/* Grid lines */}
          <line x1="10" y1="10" x2="290" y2="10" stroke="#374151" strokeWidth="1" />
          <line x1="10" y1="40" x2="290" y2="40" stroke="#374151" strokeWidth="1" />
          <line x1="10" y1="70" x2="290" y2="70" stroke="#374151" strokeWidth="1" />

          {/* Sparkline */}
          <path
            d={sparklinePath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />

          {/* Fill area */}
          <path
            d={`${sparklinePath} L 290,70 L 10,70 Z`}
            fill="rgba(59, 130, 246, 0.1)"
          />
        </svg>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-gray-400">Accuracy (last {metrics.session_cards} cards)</div>
          <div className="text-lg font-semibold text-gray-200 flex items-center">
            {(metrics.accuracy_recent * 100).toFixed(0)}%
            {metrics.trend_direction === 'improving' && (
              <span className="ml-1 text-green-400">↑</span>
            )}
            {metrics.trend_direction === 'declining' && (
              <span className="ml-1 text-red-400">↓</span>
            )}
          </div>
        </div>
        <div>
          <div className="text-gray-400">Avg Response Time</div>
          <div className="text-lg font-semibold text-gray-200">
            {Math.round(metrics.avg_response_time_ms / 1000)}s
          </div>
        </div>
      </div>

      {/* Trend indicator */}
      {metrics.trend_direction !== 'no_data' && (
        <div className="mt-2 text-xs text-gray-400">
          {metrics.trend_direction === 'improving' && 'Performance improving'}
          {metrics.trend_direction === 'declining' && 'Performance declining'}
          {metrics.trend_direction === 'stable' && 'Performance stable'}
          {metrics.trend_direction === 'insufficient_data' && 'Collecting more data'}
        </div>
      )}
    </div>
  );
};

export default RecentPerformanceChart;
