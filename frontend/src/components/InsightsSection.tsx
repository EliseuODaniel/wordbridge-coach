/** Insights Section Component */

import React, { useState } from 'react';
import WordFrequencyInsight from './WordFrequencyInsight';
import RecentPerformanceChart from './RecentPerformanceChart';
import ThemeClusterMap from './ThemeClusterMap';
import ProgressOverTimeChart from './ProgressOverTimeChart';

interface InsightsSectionProps {
  userId: string;
  cardId?: string;
  wordId?: string;
  refreshTrigger?: number;
}

const InsightsSection: React.FC<InsightsSectionProps> = ({ userId, cardId, wordId, refreshTrigger }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mt-8 border-t border-gray-700 pt-6">
      {/* Header with expand/collapse toggle */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-200">
          Insights for this word & your progress
        </h2>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center space-x-1 text-sm text-gray-400 hover:text-gray-200 transition-colors px-2 py-1 rounded hover:bg-gray-700"
        >
          <span>{isExpanded ? 'Hide insights' : 'Show insights'}</span>
          <svg
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Insights content */}
      {isExpanded && (
        <div className="space-y-4">
          {/* Grid layout for desktop - 2x2, stacked on mobile */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Row 1: WordFrequencyInsight and RecentPerformanceChart */}
            <WordFrequencyInsight userId={userId} cardId={cardId} wordId={wordId} refreshTrigger={refreshTrigger} />
            <RecentPerformanceChart userId={userId} refreshTrigger={refreshTrigger} />

            {/* Row 2: ThemeClusterMap and ProgressOverTimeChart */}
            <ThemeClusterMap userId={userId} refreshTrigger={refreshTrigger} />
            <ProgressOverTimeChart userId={userId} refreshTrigger={refreshTrigger} />
          </div>

          {/* Mobile note */}
          <div className="lg:hidden text-center text-xs text-gray-500 mt-4">
            💡 Tip: For the best experience, view insights on a larger screen
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightsSection;