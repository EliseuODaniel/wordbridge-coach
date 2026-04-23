import React from 'react';

import type { LearningContext } from '../services/apiCards';

interface LearningContextPanelProps {
  context?: LearningContext | null;
  className?: string;
}

const humanize = (value: string): string => value.replace(/_/g, ' ');

const LearningContextPanel: React.FC<LearningContextPanelProps> = ({
  context,
  className = '',
}) => {
  if (!context) {
    return null;
  }

  return (
    <div
      className={`bg-slate-900 border border-slate-700 rounded-lg p-4 ${className}`}
      data-testid="learning-context-panel"
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide">Learning focus</p>
          <h3 className="text-sm font-semibold text-slate-100">{context.current_focus}</h3>
        </div>
        <span className="px-2 py-1 bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded">
          {context.cefr_level} • {humanize(context.support_level)}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs text-slate-400 mb-1">Objetivo da sessão</p>
          <p className="text-sm text-slate-100">{context.session_goal}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-1 bg-cyan-900 bg-opacity-30 border border-cyan-700 text-cyan-200 text-xs rounded">
            Topic: {context.topic}
          </span>
          <span className="px-2 py-1 bg-teal-900 bg-opacity-30 border border-teal-700 text-teal-200 text-xs rounded">
            Feedback: {context.feedback_language}
          </span>
        </div>

        {(context.retention_signal || context.review_pressure || context.difficulty_signal || context.recommended_pace || context.next_mode_hint) && (
          <div>
            <p className="text-xs text-slate-400 mb-1">Adaptive signals</p>
            <div className="flex flex-wrap gap-2">
              {context.retention_signal && (
                <span className="px-2 py-1 bg-emerald-900/30 border border-emerald-700 text-emerald-200 text-xs rounded">
                  Retention: {humanize(context.retention_signal)}
                </span>
              )}
              {context.review_pressure && (
                <span className="px-2 py-1 bg-amber-900/30 border border-amber-700 text-amber-200 text-xs rounded">
                  Review load: {humanize(context.review_pressure)}
                </span>
              )}
              {context.difficulty_signal && (
                <span className="px-2 py-1 bg-rose-900/30 border border-rose-700 text-rose-200 text-xs rounded">
                  Difficulty: {humanize(context.difficulty_signal)}
                </span>
              )}
              {context.recommended_pace && (
                <span className="px-2 py-1 bg-indigo-900/30 border border-indigo-700 text-indigo-200 text-xs rounded">
                  Pace: {humanize(context.recommended_pace)}
                </span>
              )}
              {context.next_mode_hint && (
                <span className="px-2 py-1 bg-fuchsia-900/30 border border-fuchsia-700 text-fuchsia-200 text-xs rounded">
                  Next best mode: {humanize(context.next_mode_hint)}
                </span>
              )}
            </div>
          </div>
        )}

        <div>
          <p className="text-xs text-slate-400 mb-1">Por que este modo agora</p>
          <p className="text-xs text-slate-200 leading-relaxed">{context.why_this_now}</p>
        </div>
      </div>
    </div>
  );
};

export default LearningContextPanel;
