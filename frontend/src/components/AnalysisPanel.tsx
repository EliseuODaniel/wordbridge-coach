/**
 * AnalysisPanel Component
 *
 * Displays feedback issues (grammar, spelling, etc.) with suggestions.
 * Shows rich signals: suggested_next_words, topic/intent badges, rewrite suggestion.
 */

import React from 'react';
import type { DraftIssue } from '../services/apiChat';

interface Correction {
  mistake: string;
  fix: string;
  why: string;
}

interface TeacherAnalysis {
  rewrite: string | null;
  corrections: Correction[];
  teacher_summary: string;
  strengths: string[];
  focus_areas: string[];
  next_practice: string[];
  reflection_question: string | null;
  encouragement: string | null;
}

interface AnalysisPanelProps {
  draftText?: string;
  issues: DraftIssue[];
  micro_tip?: string | null;
  self_check_prompt?: string | null;
  encouragement?: string | null;
  suggested_next_words?: string[];
  topic?: string | null;
  intent?: string | null;
  rewrite?: string | null;
  lessonFrame?: Record<string, unknown> | null;
  studentProfile?: Record<string, unknown> | null;
  teacherAnalysis?: TeacherAnalysis | null;
  className?: string;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  draftText,
  issues,
  micro_tip,
  self_check_prompt,
  encouragement,
  suggested_next_words,
  topic,
  intent,
  rewrite,
  lessonFrame,
  studentProfile,
  teacherAnalysis,
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

  const profileStrengths = Array.isArray(studentProfile?.strengths)
    ? (studentProfile?.strengths as string[])
    : [];
  const profileWeaknesses = Array.isArray(studentProfile?.weaknesses)
    ? (studentProfile?.weaknesses as string[])
    : [];
  const recentTopics = Array.isArray(studentProfile?.recent_topics)
    ? (studentProfile?.recent_topics as string[])
    : [];
  const feedbackLanguage = typeof studentProfile?.feedback_language === 'string'
    ? studentProfile.feedback_language
    : null;
  const scaffoldingLevel = typeof studentProfile?.scaffolding_level === 'string'
    ? studentProfile.scaffolding_level
    : null;
  const cefrLevel = typeof studentProfile?.cefr_level === 'string'
    ? studentProfile.cefr_level
    : null;
  const lessonGoal = typeof lessonFrame?.learning_goal === 'string'
    ? lessonFrame.learning_goal
    : null;
  const lessonFocus = typeof lessonFrame?.primary_focus === 'string'
    ? lessonFrame.primary_focus
    : null;
  const lessonIntent = typeof lessonFrame?.expected_intent === 'string'
    ? lessonFrame.expected_intent
    : null;
  const lessonStage = typeof lessonFrame?.lesson_stage === 'string'
    ? lessonFrame.lesson_stage
    : null;
  const lessonTopic = typeof lessonFrame?.topic === 'string'
    ? lessonFrame.topic
    : null;
  const pedagogicalMetrics = studentProfile?.pedagogical_metrics
    && typeof studentProfile.pedagogical_metrics === 'object'
    && !Array.isArray(studentProfile.pedagogical_metrics)
      ? studentProfile.pedagogical_metrics as Record<string, unknown>
      : null;
  const lessonDiagnostics = lessonFrame?.diagnostics
    && typeof lessonFrame.diagnostics === 'object'
    && !Array.isArray(lessonFrame.diagnostics)
      ? lessonFrame.diagnostics as Record<string, unknown>
      : null;
  const retentionSignal = typeof pedagogicalMetrics?.retention_band === 'string'
    ? pedagogicalMetrics.retention_band
    : null;
  const reviewPressure = typeof pedagogicalMetrics?.review_pressure === 'string'
    ? pedagogicalMetrics.review_pressure
    : null;
  const difficultySignal = typeof pedagogicalMetrics?.difficulty_signal === 'string'
    ? pedagogicalMetrics.difficulty_signal
    : null;
  const recommendedPace = typeof pedagogicalMetrics?.recommended_pace === 'string'
    ? pedagogicalMetrics.recommended_pace
    : null;
  const recommendedMode = typeof pedagogicalMetrics?.recommended_mode === 'string'
    ? pedagogicalMetrics.recommended_mode
    : null;
  const cefrReadiness = typeof pedagogicalMetrics?.cefr_readiness === 'string'
    ? pedagogicalMetrics.cefr_readiness
    : null;
  const dueReviewCount = typeof pedagogicalMetrics?.due_review_count === 'number'
    ? pedagogicalMetrics.due_review_count
    : null;
  const difficultCardCount = typeof pedagogicalMetrics?.difficult_card_count === 'number'
    ? pedagogicalMetrics.difficult_card_count
    : null;
  const cardsSeenToday = typeof pedagogicalMetrics?.cards_seen_today === 'number'
    ? pedagogicalMetrics.cards_seen_today
    : null;
  const diagnosticsFocusOrigin = typeof lessonDiagnostics?.focus_origin === 'string'
    ? lessonDiagnostics.focus_origin
    : null;
  const diagnosticsRetentionScore = typeof lessonDiagnostics?.retention_score === 'number'
    ? lessonDiagnostics.retention_score
    : null;
  const humanizeMetric = (value: string): string => value.replace(/_/g, ' ');

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

      {self_check_prompt && (
        <div className="bg-sky-900 bg-opacity-20 border border-sky-700 rounded-lg p-3 mb-3">
          <p className="text-xs text-sky-300 mb-1">🧠 Self-check</p>
          <p className="text-sm text-sky-100">{self_check_prompt}</p>
        </div>
      )}

      {encouragement && (
        <div className="bg-emerald-900 bg-opacity-20 border border-emerald-700 rounded-lg p-3 mb-3">
          <p className="text-sm text-emerald-100">🌱 {encouragement}</p>
        </div>
      )}

      {studentProfile && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 mb-3">
          <p className="text-xs text-gray-400 mb-2">Coach memory</p>
          {(cefrLevel || feedbackLanguage || scaffoldingLevel) && (
            <div className="flex flex-wrap gap-2 mb-3">
              {cefrLevel && (
                <span className="px-2 py-1 bg-gray-700 text-gray-200 text-xs rounded border border-gray-600">
                  CEFR: {cefrLevel}
                </span>
              )}
              {feedbackLanguage && (
                <span className="px-2 py-1 bg-teal-900 bg-opacity-30 border border-teal-700 text-teal-200 text-xs rounded">
                  Feedback: {feedbackLanguage}
                </span>
              )}
              {scaffoldingLevel && (
                <span className="px-2 py-1 bg-amber-900 bg-opacity-30 border border-amber-700 text-amber-200 text-xs rounded">
                  Support: {scaffoldingLevel.replace(/_/g, ' ')}
                </span>
              )}
            </div>
          )}

          {profileStrengths.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Remembered strengths:</p>
              {profileStrengths.map((strength, idx) => (
                <p key={idx} className="text-xs text-emerald-200 mb-1">• {strength}</p>
              ))}
            </div>
          )}

          {profileWeaknesses.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Current focus memory:</p>
              {profileWeaknesses.map((focus, idx) => (
                <p key={idx} className="text-xs text-amber-200 mb-1">• {focus}</p>
              ))}
            </div>
          )}

          {recentTopics.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-1">Recent topics:</p>
              <div className="flex flex-wrap gap-2">
                {recentTopics.map((recentTopic, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-slate-700 text-slate-200 text-xs rounded border border-slate-600"
                  >
                    {recentTopic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {(retentionSignal || reviewPressure || difficultySignal || recommendedPace || recommendedMode || cefrReadiness) && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-400 mb-2">Adaptive metrics:</p>
              <div className="flex flex-wrap gap-2 mb-2">
                {retentionSignal && (
                  <span className="px-2 py-1 bg-emerald-900/30 border border-emerald-700 text-emerald-200 text-xs rounded">
                    Retention: {humanizeMetric(retentionSignal)}
                  </span>
                )}
                {reviewPressure && (
                  <span className="px-2 py-1 bg-amber-900/30 border border-amber-700 text-amber-200 text-xs rounded">
                    Review load: {humanizeMetric(reviewPressure)}
                  </span>
                )}
                {difficultySignal && (
                  <span className="px-2 py-1 bg-rose-900/30 border border-rose-700 text-rose-200 text-xs rounded">
                    Difficulty: {humanizeMetric(difficultySignal)}
                  </span>
                )}
                {recommendedPace && (
                  <span className="px-2 py-1 bg-indigo-900/30 border border-indigo-700 text-indigo-200 text-xs rounded">
                    Pace: {humanizeMetric(recommendedPace)}
                  </span>
                )}
                {recommendedMode && (
                  <span className="px-2 py-1 bg-fuchsia-900/30 border border-fuchsia-700 text-fuchsia-200 text-xs rounded">
                    Next best mode: {humanizeMetric(recommendedMode)}
                  </span>
                )}
              </div>
              {(dueReviewCount !== null || difficultCardCount !== null || cardsSeenToday !== null || cefrReadiness) && (
                <div className="space-y-1">
                  {cefrReadiness && (
                    <p className="text-xs text-sky-200">CEFR readiness: {humanizeMetric(cefrReadiness)}</p>
                  )}
                  {dueReviewCount !== null && (
                    <p className="text-xs text-gray-300">Due reviews now: {dueReviewCount}</p>
                  )}
                  {difficultCardCount !== null && (
                    <p className="text-xs text-gray-300">Cards under strain: {difficultCardCount}</p>
                  )}
                  {cardsSeenToday !== null && (
                    <p className="text-xs text-gray-300">Cards seen today: {cardsSeenToday}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {lessonFrame && (lessonGoal || lessonFocus || lessonIntent || lessonStage || lessonTopic) && (
        <div className="bg-slate-900 bg-opacity-40 border border-slate-700 rounded-lg p-3 mb-3">
          <p className="text-xs text-slate-300 mb-2">Current lesson frame</p>

          {(lessonStage || lessonTopic) && (
            <div className="flex flex-wrap gap-2 mb-3">
              {lessonStage && (
                <span className="px-2 py-1 bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded">
                  Stage: {lessonStage.replace(/_/g, ' ')}
                </span>
              )}
              {lessonTopic && (
                <span className="px-2 py-1 bg-cyan-900 bg-opacity-30 border border-cyan-700 text-cyan-200 text-xs rounded">
                  Topic: {lessonTopic}
                </span>
              )}
            </div>
          )}

          {lessonGoal && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Turn goal:</p>
              <p className="text-xs text-slate-100">{lessonGoal}</p>
            </div>
          )}

          {lessonFocus && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Primary focus:</p>
              <p className="text-xs text-amber-200">{lessonFocus}</p>
            </div>
          )}

          {lessonIntent && (
            <div>
              <p className="text-xs text-gray-400 mb-1">Expected intent:</p>
              <p className="text-xs text-sky-100">{lessonIntent.replace(/_/g, ' ')}</p>
            </div>
          )}

          {(diagnosticsFocusOrigin || diagnosticsRetentionScore !== null) && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <p className="text-xs text-gray-400 mb-1">Frame diagnostics:</p>
              {diagnosticsFocusOrigin && (
                <p className="text-xs text-slate-200 mb-1">
                  Focus source: {humanizeMetric(diagnosticsFocusOrigin)}
                </p>
              )}
              {diagnosticsRetentionScore !== null && (
                <p className="text-xs text-slate-200">
                  Retention score: {Math.round(diagnosticsRetentionScore * 100)}%
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Professor (LLM) Analysis */}
      {teacherAnalysis && (
        <div className="bg-purple-900 bg-opacity-20 border border-purple-600 rounded-lg p-3 mb-3">
          <p className="text-xs text-purple-300 mb-2 font-semibold">👨‍🏫 Professor (LLM)</p>

          {/* Rewrite */}
          {teacherAnalysis.rewrite && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Better version:</p>
              <p className="text-sm text-purple-100 italic">"{teacherAnalysis.rewrite}"</p>
            </div>
          )}

          {/* Corrections */}
          {teacherAnalysis.corrections && teacherAnalysis.corrections.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-2">Corrections:</p>
              {teacherAnalysis.corrections.map((correction, idx) => (
                <div key={idx} className="mb-2 pb-2 border-b border-purple-700 last:border-0 last:mb-0">
                  <p className="text-xs text-red-300 mb-0.5">❌ {correction.mistake}</p>
                  <p className="text-xs text-green-300 mb-0.5">✓ {correction.fix}</p>
                  <p className="text-xs text-gray-400">{correction.why}</p>
                </div>
              ))}
            </div>
          )}

          {/* Teacher Summary */}
          {teacherAnalysis.teacher_summary && (
            <div className="mb-3">
              <p className="text-xs text-blue-200">💡 {teacherAnalysis.teacher_summary}</p>
            </div>
          )}

          {teacherAnalysis.strengths && teacherAnalysis.strengths.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Strengths:</p>
              {teacherAnalysis.strengths.map((strength, idx) => (
                <p key={idx} className="text-xs text-emerald-200 mb-1">• {strength}</p>
              ))}
            </div>
          )}

          {teacherAnalysis.focus_areas && teacherAnalysis.focus_areas.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Focus next:</p>
              {teacherAnalysis.focus_areas.map((focusArea, idx) => (
                <p key={idx} className="text-xs text-amber-200 mb-1">• {focusArea}</p>
              ))}
            </div>
          )}

          {/* Next Practice */}
          {teacherAnalysis.next_practice && teacherAnalysis.next_practice.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Practice these:</p>
              {teacherAnalysis.next_practice.map((practice, idx) => (
                <p key={idx} className="text-xs text-gray-300 mb-1">• {practice}</p>
              ))}
            </div>
          )}

          {teacherAnalysis.reflection_question && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">Reflect:</p>
              <p className="text-xs text-sky-100">{teacherAnalysis.reflection_question}</p>
            </div>
          )}

          {teacherAnalysis.encouragement && (
            <div>
              <p className="text-xs text-emerald-200">🌱 {teacherAnalysis.encouragement}</p>
            </div>
          )}
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
