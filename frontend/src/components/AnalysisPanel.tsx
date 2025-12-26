/**
 * AnalysisPanel Component
 *
 * Displays feedback issues (grammar, spelling, etc.) with suggestions.
 * Shows rich signals: suggested_next_words, topic/intent badges, rewrite suggestion.
 */

import React from 'react';
import type { DraftIssue } from '../services/api';

interface AnalysisPanelProps {
  draftText?: string;
  issues: DraftIssue[];
  micro_tip?: string | null;
  suggested_next_words?: string[];
  topic?: string | null;
  intent?: string | null;
  rewrite?: string | null;
  className?: string;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  draftText,
  issues,
  micro_tip,
  suggested_next_words,
  topic,
  intent,
  rewrite,
  className = ''
}) => {
  // REMOVED: Early returns for issues.length === 0
  // Now always render rich signals first, then issues

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

  const getHighlightClass = (category: string): string => {
    const classes: Record<string, string> = {
      spelling: 'bg-red-900/50 border-b-2 border-red-500 text-red-100',
      grammar: 'bg-yellow-900/50 border-b-2 border-yellow-500 text-yellow-100',
      syntax: 'bg-orange-900/50 border-b-2 border-orange-500 text-orange-100',
      semantic: 'bg-purple-900/50 border-b-2 border-purple-500 text-purple-100',
      style: 'bg-blue-900/50 border-b-2 border-blue-500 text-blue-100'
    };
    return classes[category] || 'bg-gray-700/50 border-b-2 border-gray-500';
  };

  /**
   * Render text with highlighted error spans
   */
  const renderHighlightedText = (text: string, issues: DraftIssue[]): React.ReactNode => {
    if (!text) return null;

    // Extract all highlight_spans with category
    const spans = issues.flatMap(issue =>
      (issue.highlight_spans || []).map(span => ({
        start: span.start,
        end: span.end,
        category: issue.category,
        title: issue.title
      }))
    );

    // Filter and sort spans
    const validSpans = spans
      .filter(s => s.start >= 0 && s.end <= text.length && s.start < s.end)
      .sort((a, b) => a.start - b.start);

    if (validSpans.length === 0) {
      return <span className="text-gray-300">{text}</span>;
    }

    // Render text with <span> wrappers for highlights
    let lastEnd = 0;
    const parts: React.ReactNode[] = [];

    for (const span of validSpans) {
      // Skip overlapping spans
      if (span.start < lastEnd) continue;

      // Text before highlight
      if (span.start > lastEnd) {
        parts.push(
          <span key={`text-${lastEnd}`} className="text-gray-300">
            {text.slice(lastEnd, span.start)}
          </span>
        );
      }

      // Highlighted text
      parts.push(
        <span
          key={`highlight-${span.start}-${span.end}`}
          className={getHighlightClass(span.category)}
          title={span.title}
        >
          {text.slice(span.start, span.end)}
        </span>
      );

      lastEnd = span.end;
    }

    // Remaining text
    if (lastEnd < text.length) {
      parts.push(
        <span key={`text-${lastEnd}`} className="text-gray-300">
          {text.slice(lastEnd)}
        </span>
      );
    }

    return <>{parts}</>;
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Feedback</h3>

      {/* Your text with error highlights */}
      {draftText && draftText.trim() && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 mb-3">
          <p className="text-xs text-gray-400 mb-2">Seu texto:</p>
          <p className="text-sm leading-relaxed">
            {renderHighlightedText(draftText, issues)}
          </p>
        </div>
      )}

      {/* Rich signals - ALWAYS RENDER THESE FIRST */}
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

      {/* Micro tip */}
      {micro_tip && (
        <div className="bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg p-3 mb-3">
          <p className="text-sm text-blue-200">💡 {micro_tip}</p>
        </div>
      )}

      {/* Issues - render if present, otherwise show success message */}
      {issues.length > 0 ? (
        issues.map((issue, index) => (
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

            {/* Error snippet from draft text */}
            {draftText && issue.highlight_spans && issue.highlight_spans.length > 0 && (
              <div className="mb-2 bg-gray-900 rounded px-2 py-1">
                <p className="text-xs text-gray-500 mb-1">Error in:</p>
                <p className="text-sm">
                  {issue.highlight_spans.map((span, si) => (
                    <span
                      key={si}
                      className={`px-1 py-0.5 rounded ${getHighlightClass(issue.category)}`}
                    >
                      {draftText.slice(span.start, span.end)}
                    </span>
                  ))}
                </p>
              </div>
            )}

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
        ))
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">✅ No issues detected. Great job!</p>
        </div>
      )}
    </div>
  );
};

export default AnalysisPanel;
