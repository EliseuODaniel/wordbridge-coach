/** Word Frequency Insight Component - Refactored with Coverage Curve */

import React, { useState, useEffect, useMemo } from 'react';
import {
  insightsApi,
  getApiErrorCode,
  getApiErrorStatus,
  type WordInsightResponse,
} from '../services/api';
import { withRetry } from '../utils/apiUtils';

interface CoveragePoint {
  rank: number;
  coverage_pct: number;
}

interface WordFrequencyInsightProps {
  userId: string;
  cardId?: string;
  wordId?: string;
  refreshTrigger?: number;
  className?: string;
}

const WordFrequencyInsight: React.FC<WordFrequencyInsightProps> = ({ cardId, wordId, refreshTrigger, className = '' }) => {
  const [insight, setInsight] = useState<WordInsightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsight = async () => {
      // Prioritize wordId over cardId since wordId endpoint works
      const id = wordId || cardId;
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        let data;
        if (wordId) {
          // Use wordId endpoint (works correctly)
          data = await withRetry(
            () => insightsApi.getWordInsights(wordId),
            { maxRetries: 2, baseDelay: 1000 }
          );
        } else {
          // Fallback to cardId endpoint (may not work)
          data = await withRetry(
            () => insightsApi.getWordInsightsByCard(id),
            { maxRetries: 2, baseDelay: 1000 }
          );
        }
        setInsight(data);
      } catch (err) {
        console.error('Error fetching word insights after retries:', err);
        const status = getApiErrorStatus(err);
        const code = getApiErrorCode(err);

        if (status === 404) {
          setError('No frequency data available for this word');
        } else if (typeof status === 'number' && status >= 500) {
          setError('Server temporarily unavailable - please refresh');
        } else if (code === 'NETWORK_ERROR') {
          setError('Network error - check your connection');
        } else {
          setError('Failed to load word frequency data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchInsight();
  }, [cardId, wordId, refreshTrigger]);

  // Generate coverage curve based on the word's rank and coverage
  const coverageCurve = useMemo(() => {
    if (!insight || !insight.rank || insight.coverage_pct === undefined) return [];

    const { rank, coverage_pct } = insight;

    // Generate base logarithmic-scale coverage curve points
    const baseCurvePoints: CoveragePoint[] = [
      { rank: 1, coverage_pct: 5.0 },
      { rank: 10, coverage_pct: 25.0 },
      { rank: 100, coverage_pct: 55.0 },
      { rank: 500, coverage_pct: 70.0 },
      { rank: 1000, coverage_pct: 80.0 },
      { rank: 5000, coverage_pct: 92.0 },
      { rank: 10000, coverage_pct: 99.0 }
    ];

    // Insert the current word's position maintaining order
    let currentPointInserted = false;
    const curvePoints: CoveragePoint[] = [];

    for (const point of baseCurvePoints) {
      // Add current point before this base point if its rank is smaller
      if (!currentPointInserted && rank < point.rank) {
        curvePoints.push({ rank, coverage_pct: coverage_pct ?? 0 });
        currentPointInserted = true;
      }
      curvePoints.push(point);
    }

    // Add current point at the end if its rank is larger than all base points
    if (!currentPointInserted) {
      curvePoints.push({ rank, coverage_pct: coverage_pct ?? 0 });
    }

    // Ensure monotonic increase: adjust coverage_pct to be cumulative
    let maxCoverage = 0;
    return curvePoints.map(point => {
      maxCoverage = Math.max(maxCoverage, point.coverage_pct);
      return { ...point, coverage_pct: maxCoverage };
    });
  }, [insight]);

  // Calculate chart dimensions and scale
  const chartWidth = 320;
  const chartHeight = 180;
  const padding = { top: 20, right: 40, bottom: 50, left: 40 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  // Scale functions
  const xScale = (rank: number) => {
    // Logarithmic scale for ranks 1-10000
    const logRank = Math.log10(Math.max(1, rank));
    const logMax = 4; // log10(10000)
    return padding.left + (logRank / logMax) * plotWidth;
  };

  const yScale = (coverage: number) => {
    return padding.top + plotHeight - (coverage / 100) * plotHeight;
  };

  // Format rank labels for display
  const formatRankLabel = (rank: number) => {
    if (rank >= 1000) return `${rank / 1000}k`;
    return rank.toString();
  };

  // Generate path for the coverage curve
  const generatePath = () => {
    return coverageCurve
      .map((point, index) => {
        const x = xScale(point.rank);
        const y = yScale(point.coverage_pct);
        return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
      })
      .join(' ');
  };

  // Generate area path (curve + bottom line)
  const generateAreaPath = () => {
    const curvePath = coverageCurve
      .map((point, index) => {
        const x = xScale(point.rank);
        const y = yScale(point.coverage_pct);
        return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
      })
      .join(' ');

    const bottomRight = `${padding.left + plotWidth},${padding.top + plotHeight}`;
    const bottomLeft = `${padding.left},${padding.top + plotHeight}`;

    return `${curvePath} L ${bottomRight} L ${bottomLeft} Z`;
  };

  // Calculate top percentage
  const topPercent = insight && insight.rank ? ((insight.rank / 10000) * 100).toFixed(1) : '0';

  // Get description based on rank
  const getFrequencyDescription = (rank: number) => {
    if (rank <= 500) {
      return "This word is among the 500 most frequent words in English.";
    } else if (rank <= 3000) {
      return "This word is a fairly common word in everyday English.";
    } else {
      return "This word is less frequent but still useful to know.";
    }
  };

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
          <div className="h-44 bg-gray-700 rounded mb-3"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-700 rounded w-2/3"></div>
            <div className="h-3 bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !insight) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
        <h3 className="text-sm font-medium text-gray-300 mb-2">How common is this word?</h3>
        <div className="text-gray-500 text-sm">
          {error || 'Frequency data for this word is not available yet.'}
        </div>
      </div>
    );
  }

  const { word, rank, coverage_pct } = insight;
  const currentX = xScale(rank || 1);
  const currentY = yScale(coverage_pct || 0);

  return (
    <div className={`bg-gray-800 rounded-lg p-4 border border-gray-700 ${className}`}>
      <h3 className="text-sm font-medium text-gray-300 mb-4">How common is this word?</h3>

      {/* Coverage Chart */}
      <div className="mb-4">
        <svg
          width={chartWidth}
          height={chartHeight}
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full"
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((pct) => {
            const y = yScale(pct);
            return (
              <line
                key={`grid-h-${pct}`}
                x1={padding.left}
                y1={y}
                x2={padding.left + plotWidth}
                y2={y}
                stroke="#374151"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            );
          })}

          {/* Grid lines for X (logarithmic) */}
          {[1, 10, 100, 1000, 10000].map((rankVal) => {
            const x = xScale(rankVal);
            return (
              <line
                key={`grid-v-${rankVal}`}
                x1={x}
                y1={padding.top}
                x2={x}
                y2={padding.top + plotHeight}
                stroke="#374151"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            );
          })}

          {/* Area under the curve */}
          <path
            d={generateAreaPath()}
            fill="url(#coverageGradient)"
            opacity="0.3"
          />

          {/* Coverage curve */}
          <path
            d={generatePath()}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />

          {/* Current word point */}
          <circle
            cx={currentX}
            cy={currentY}
            r="5"
            fill="#3b82f6"
            stroke="#1e40af"
            strokeWidth="2"
          />

          {/* Vertical line from current word to X axis */}
          <line
            x1={currentX}
            y1={currentY}
            x2={currentX}
            y2={padding.top + plotHeight}
            stroke="#3b82f6"
            strokeWidth="1"
            strokeDasharray="4,2"
            opacity="0.6"
          />

          {/* Y-axis labels */}
          {[0, 25, 50, 75, 100].map((pct) => {
            const y = yScale(pct);
            return (
              <text
                key={`label-y-${pct}`}
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                fill="#9ca3af"
                fontSize="11"
              >
                {pct}%
              </text>
            );
          })}

          {/* X-axis labels */}
          {[1, 10, 100, 1000, 10000].map((rankVal) => {
            const x = xScale(rankVal);
            return (
              <text
                key={`label-x-${rankVal}`}
                x={x}
                y={padding.top + plotHeight + 20}
                textAnchor="middle"
                fill="#9ca3af"
                fontSize="11"
              >
                {formatRankLabel(rankVal)}
              </text>
            );
          })}

          {/* Gradient definition */}
          <defs>
            <linearGradient id="coverageGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Word Information */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-100">{word}</span>
          <span className="text-sm text-gray-400">Rank #{rank}</span>
        </div>

        <div className="text-sm text-gray-300">
          This word: rank <span className="font-semibold text-blue-400">#{rank}</span> (top <span className="font-semibold text-blue-400">{topPercent}%</span>)
        </div>

        <div className="text-sm text-gray-300">
          Coverage up to here: <span className="font-semibold text-green-400">{(coverage_pct ?? 0).toFixed(1)}%</span> of word usage
        </div>

        <div className="text-xs text-gray-400 italic">
          {getFrequencyDescription(rank || 0)}
        </div>
      </div>
    </div>
  );
};

export default WordFrequencyInsight;
