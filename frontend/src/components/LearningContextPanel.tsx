import React from 'react';

import type { LearningContext } from '../services/apiCards';
import InfoTooltip from './InfoTooltip';

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
    <section
      className={`surface-soft flex items-center gap-3 p-3 ${className}`}
      data-testid="learning-context-panel"
    >
      <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-200">
        <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16ZM20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" />
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-500">Foco atual</p>
        <h3 className="truncate text-sm font-semibold text-gray-100">{context.current_focus}</h3>
      </div>
      <span className="status-pill min-h-7 whitespace-nowrap px-2">{context.cefr_level} · {humanize(context.support_level)}</span>
      <InfoTooltip label="Detalhes do foco pedagógico">
        <strong className="mb-1 block text-white">Objetivo da sessão</strong>
        <span className="block">{context.session_goal}</span>
        <span className="mt-2 block text-gray-400">Tema: {context.topic} · feedback em {context.feedback_language}</span>
        <span className="mt-2 block">{context.why_this_now}</span>
        {(context.retention_signal || context.review_pressure || context.recommended_pace) && (
          <span className="mt-2 block text-primary-200">
            {context.retention_signal && `Retenção: ${humanize(context.retention_signal)}`}
            {context.review_pressure && ` · Revisões: ${humanize(context.review_pressure)}`}
            {context.recommended_pace && ` · Ritmo: ${humanize(context.recommended_pace)}`}
          </span>
        )}
      </InfoTooltip>
    </section>
  );
};

export default LearningContextPanel;
