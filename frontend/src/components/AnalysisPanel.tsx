/**
 * AnalysisPanel Component
 *
 * Displays feedback issues (grammar, spelling, etc.) with suggestions.
 * Shows rich signals: suggested_next_words, topic/intent badges, rewrite suggestion.
 */

import React from 'react';
import type { DraftIssue } from '../services/api';

interface AnalysisPanelProps {
  issues: DraftIssue[];
  micro_tip?: string | null;
  suggested_next_words?: string[];
  topic?: string | null;
  intent?: string | null;
  rewrite?: string | null;
  className?: string;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  issues,
  micro_tip,
  suggested_next_words,
  topic,
  intent,
  rewrite,
  className = ''
}) => {
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

      {/* Context tags: topic/intent */}
      {(topic || intent) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {topic && (
            <span className="px-2 py-1 bg-purple-900 bg-opacity-30 border border-purple-600 text-purple-200 text-xs rounded">
              🏷️ Topic: {topic}
            </span>
          )}
          {intent && (
            <span className="px-2 py-1 bg-indigo-900 bg-opacity-30 border border-indigo-600 text-indigo-200 text-xs rounded">
              🎯 Intent: {intent}
            </span>
          )}
        </div>
      )}

      {/* Suggested next words */}
      {suggested_next_words && suggested_next_words.length > 0 && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 mb-3">
          <p className="text-xs text-gray-400 mb-2">✨ Try these words:</p>
          <div className="flex flex-wrap gap-2">
            {suggested_next_words.map((word, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-blue-900 bg-opacity-40 border border-blue-600 text-blue-200 text-sm rounded cursor-pointer hover:bg-opacity-60 transition"
              >
                {word}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Rewrite suggestion */}
      {rewrite && (
        <div className="bg-green-900 bg-opacity-20 border border-green-600 rounded-lg p-3 mb-3">
          <p className="text-xs text-green-300 mb-1">💡 Suggested rewrite:</p>
          <p className="text-sm text-green-100 italic">"{rewrite}"</p>
        </div>
      )}

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
