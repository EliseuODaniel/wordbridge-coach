/** Insights Section Component */

import React, { useState } from 'react';
import WordFrequencyInsight from './WordFrequencyInsight';
import RecentPerformanceChart from './RecentPerformanceChart';
import ThemeClusterMap from './ThemeClusterMap';
import ProgressOverTimeChart from './ProgressOverTimeChart';
import InfoTooltip from './InfoTooltip';

interface InsightsSectionProps {
  userId: string;
  cardId?: string;
  wordId?: string;
  refreshTrigger?: number;
}

const InsightsSection: React.FC<InsightsSectionProps> = ({ userId, cardId, wordId, refreshTrigger }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <section className="mt-5">
      <div className="surface-soft flex items-center justify-between gap-3 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <h2 className="truncate text-sm font-semibold text-gray-200">Insights e progresso</h2>
          <InfoTooltip label="Sobre os insights">Explore frequência, desempenho recente, temas e evolução ao longo do tempo.</InfoTooltip>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="btn btn-secondary min-h-9 px-3 text-xs"
          aria-expanded={isExpanded}
        >
          <span>{isExpanded ? 'Ocultar' : 'Explorar'}</span>
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

      {isExpanded && (
        <div className="mt-3 space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <WordFrequencyInsight userId={userId} cardId={cardId} wordId={wordId} refreshTrigger={refreshTrigger} />
            <RecentPerformanceChart userId={userId} refreshTrigger={refreshTrigger} />
            <ThemeClusterMap userId={userId} refreshTrigger={refreshTrigger} />
            <ProgressOverTimeChart userId={userId} refreshTrigger={refreshTrigger} />
          </div>
        </div>
      )}
    </section>
  );
};

export default InsightsSection;
