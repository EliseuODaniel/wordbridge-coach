/**
 * AnalysisPanel Component
 *
 * Displays feedback issues (grammar, spelling, etc.) with suggestions.
 * When no issues, shows micro_tip if available.
 */

import React from 'react';
import type { DraftIssue } from '../services/api';

interface AnalysisPanelProps {
  issues: DraftIssue[];
  micro_tip?: string | null;
  className?: string;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ issues, micro_tip, className = '' }) => {
  // Case 1: No issues + micro_tip available
  if (issues.length === 0 && micro_tip) {
    return (
      <div className={`text-center py-4 ${className}`}>
        <div className="bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg p-3 mb-2">
          <p className="text-sm text-blue-200">💡 {micro_tip}</p>
        </div>
        <p className="text-gray-500 text-xs">No issues detected. Keep up the good work!</p>
      </div>
    );
  }

  // Case 2: No issues + no micro_tip
  if (issues.length === 0) {
    return (
      <div className={`text-center py-4 ${className}`}>
        <p className="text-gray-500 text-sm">No issues detected. Great job!</p>
      </div>
    );
  }

  // Case 3: Has issues
  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      spelling: '🔤',
      grammar: '📝',
      syntax: '🔗',
      semantic: '💭',
      style: '✨'
    };
    return icons[category] || '💡';
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      spelling: 'border-red-500 bg-red-900 bg-opacity-20',
      grammar: 'border-yellow-500 bg-yellow-900 bg-opacity-20',
      syntax: 'border-orange-500 bg-orange-900 bg-opacity-20',
      semantic: 'border-purple-500 bg-purple-900 bg-opacity-20',
      style: 'border-blue-500 bg-blue-900 bg-opacity-20'
    };
    return colors[category] || 'border-gray-500 bg-gray-800';
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Feedback</h3>

      {issues.map((issue, index) => (
        <div
          key={index}
          className={`border-l-4 ${getCategoryColor(issue.category)} rounded-r-lg p-3`}
        >
          {/* Issue header */}
          <div className="flex items-start gap-2 mb-2">
            <span className="text-xl">{getCategoryIcon(issue.category)}</span>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-200">{issue.title}</h4>
              <p className="text-xs text-gray-400 capitalize">{issue.category}</p>
            </div>
          </div>

          {/* Explanation */}
          <p className="text-sm text-gray-300 mb-2">{issue.explanation}</p>

          {/* Suggestions */}
          {issue.suggestions && issue.suggestions.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-400 mb-1">Suggestions:</p>
              <div className="flex flex-wrap gap-1.5">
                {issue.suggestions.map((suggestion, si) => (
                  <span
                    key={si}
                    className="px-2 py-1 bg-gray-700 text-gray-200 text-xs rounded border border-gray-600"
                  >
                    {suggestion}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default AnalysisPanel;
