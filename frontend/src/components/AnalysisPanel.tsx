import React from 'react';

import type { DraftIssue } from '../services/apiChat';
import AnalysisDisclosure from './AnalysisDisclosure';
import InfoTooltip from './InfoTooltip';

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

const categoryLabels: Record<string, string> = {
  spelling: 'Ortografia',
  grammar: 'Gramática',
  syntax: 'Sintaxe',
  semantic: 'Sentido',
  style: 'Estilo',
};

const categoryStyles: Record<string, string> = {
  spelling: 'border-red-400/25 bg-red-400/5 text-red-200',
  grammar: 'border-amber-400/25 bg-amber-400/5 text-amber-200',
  syntax: 'border-orange-400/25 bg-orange-400/5 text-orange-200',
  semantic: 'border-violet-400/25 bg-violet-400/5 text-violet-200',
  style: 'border-sky-400/25 bg-sky-400/5 text-sky-200',
};

const highlightStyles: Record<string, string> = {
  spelling: 'border-b border-red-400 bg-red-400/10 text-red-100',
  grammar: 'border-b border-amber-400 bg-amber-400/10 text-amber-100',
  syntax: 'border-b border-orange-400 bg-orange-400/10 text-orange-100',
  semantic: 'border-b border-violet-400 bg-violet-400/10 text-violet-100',
  style: 'border-b border-sky-400 bg-sky-400/10 text-sky-100',
};

const humanize = (value: string): string => value.replace(/_/g, ' ');

const stringValue = (record: Record<string, unknown> | null | undefined, key: string) =>
  typeof record?.[key] === 'string' ? (record[key] as string) : null;

const numberValue = (record: Record<string, unknown> | null | undefined, key: string) =>
  typeof record?.[key] === 'number' ? (record[key] as number) : null;

const stringList = (record: Record<string, unknown> | null | undefined, key: string) =>
  Array.isArray(record?.[key]) ? (record[key] as string[]) : [];

const nestedRecord = (record: Record<string, unknown> | null | undefined, key: string) => {
  const value = record?.[key];
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
};

const renderHighlightedText = (text: string, issues: DraftIssue[]): React.ReactNode => {
  const spans = issues
    .flatMap((issue) =>
      (issue.highlight_spans || []).map((span) => ({ ...span, category: issue.category, title: issue.title })),
    )
    .filter((span) => span.start >= 0 && span.end <= text.length && span.start < span.end)
    .sort((left, right) => left.start - right.start);

  if (spans.length === 0) {
    return text;
  }

  let lastEnd = 0;
  const parts: React.ReactNode[] = [];

  spans.forEach((span) => {
    if (span.start < lastEnd) return;
    if (span.start > lastEnd) parts.push(text.slice(lastEnd, span.start));
    parts.push(
      <span
        key={`${span.start}-${span.end}-${span.category}`}
        className={highlightStyles[span.category] || highlightStyles.style}
        title={span.title}
      >
        {text.slice(span.start, span.end)}
      </span>,
    );
    lastEnd = span.end;
  });

  if (lastEnd < text.length) parts.push(text.slice(lastEnd));
  return parts;
};

const CompactList = ({ items, tone = 'text-gray-300' }: { items: string[]; tone?: string }) => (
  <ul className={`space-y-1 text-xs leading-5 ${tone}`}>
    {items.map((item, index) => <li key={`${item}-${index}`}>• {item}</li>)}
  </ul>
);

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
  className = '',
}) => {
  const headingId = React.useId();
  const profileStrengths = stringList(studentProfile, 'strengths');
  const profileWeaknesses = stringList(studentProfile, 'weaknesses');
  const recentTopics = stringList(studentProfile, 'recent_topics');
  const cefrLevel = stringValue(studentProfile, 'cefr_level');
  const feedbackLanguage = stringValue(studentProfile, 'feedback_language');
  const scaffoldingLevel = stringValue(studentProfile, 'scaffolding_level');

  const lessonGoal = stringValue(lessonFrame, 'learning_goal');
  const lessonFocus = stringValue(lessonFrame, 'primary_focus');
  const lessonIntent = stringValue(lessonFrame, 'expected_intent');
  const lessonStage = stringValue(lessonFrame, 'lesson_stage');
  const lessonTopic = stringValue(lessonFrame, 'topic');

  const metrics = nestedRecord(studentProfile, 'pedagogical_metrics');
  const diagnostics = nestedRecord(lessonFrame, 'diagnostics');
  const metricSignals = [
    ['Retenção', stringValue(metrics, 'retention_band')],
    ['Revisões', stringValue(metrics, 'review_pressure')],
    ['Dificuldade', stringValue(metrics, 'difficulty_signal')],
    ['Ritmo', stringValue(metrics, 'recommended_pace')],
    ['Próximo modo', stringValue(metrics, 'recommended_mode')],
    ['Prontidão CEFR', stringValue(metrics, 'cefr_readiness')],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]));
  const metricCounts = [
    ['Revisões', numberValue(metrics, 'due_review_count')],
    ['Em dificuldade', numberValue(metrics, 'difficult_card_count')],
    ['Vistos hoje', numberValue(metrics, 'cards_seen_today')],
  ].filter((entry): entry is [string, number] => entry[1] !== null);
  const guidance = micro_tip || self_check_prompt || encouragement;
  const feedbackIssueCount = Math.max(issues.length, teacherAnalysis?.corrections?.length || 0);
  const hasWritingDetails = issues.length > 0 || Boolean(micro_tip || self_check_prompt || encouragement);
  const contextMeta = [topic, intent].filter(Boolean).join(' · ');
  const memoryMeta = [cefrLevel, scaffoldingLevel && humanize(scaffoldingLevel)].filter(Boolean).join(' · ');
  const lessonMeta = [lessonTopic, lessonStage && humanize(lessonStage)].filter(Boolean).join(' · ');

  return (
    <section className={`space-y-2.5 ${className}`} aria-labelledby={headingId}>
      <div className="flex min-h-8 items-center gap-2">
        <h3 id={headingId} className="min-w-0 flex-1 text-sm font-semibold text-gray-200">Feedback</h3>
        <span className={`status-pill min-h-6 px-2 py-0.5 text-[10px] ${feedbackIssueCount > 0 ? 'border-amber-400/20 bg-amber-400/10 text-amber-200' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200'}`}>
          {feedbackIssueCount > 0 ? `${feedbackIssueCount} ${feedbackIssueCount === 1 ? 'ajuste' : 'ajustes'}` : 'Em dia'}
        </span>
        <InfoTooltip label="Como o feedback está organizado">
          O essencial fica visível. Abra as seções somente quando quiser consultar correções, memória pedagógica ou detalhes da aula.
        </InfoTooltip>
      </div>

      {(contextMeta || guidance || teacherAnalysis?.teacher_summary) && (
        <div className="rounded-xl border border-primary-400/15 bg-primary-400/[0.055] p-3">
          {contextMeta && <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-primary-300">{contextMeta}</p>}
          <p className="text-xs leading-5 text-gray-200">
            {guidance || teacherAnalysis?.teacher_summary}
          </p>
        </div>
      )}

      {draftText && draftText.trim() && (
        <div className="rounded-xl border border-white/[0.07] bg-gray-950/35 px-3 py-2.5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-gray-500">Seu texto</p>
          <p className="line-clamp-3 text-xs leading-5 text-gray-300">{renderHighlightedText(draftText, issues)}</p>
        </div>
      )}

      {(rewrite || teacherAnalysis?.rewrite) && (
        <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/[0.055] px-3 py-2.5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-300">Versão sugerida</p>
          <p className="line-clamp-3 text-xs italic leading-5 text-emerald-100">“{rewrite || teacherAnalysis?.rewrite}”</p>
        </div>
      )}

      {suggested_next_words && suggested_next_words.length > 0 && (
        <div className="flex flex-wrap gap-1.5" aria-label="Próximas palavras sugeridas">
          {suggested_next_words.slice(0, 5).map((word) => (
            <span key={word} className="status-pill min-h-6 px-2 py-0.5 text-[10px] text-sky-200">{word}</span>
          ))}
        </div>
      )}

      {hasWritingDetails && (
        <AnalysisDisclosure
          title="Ajustes de escrita"
          meta={issues.length > 0 ? `${issues.length} encontrados` : 'orientações'}
        >
          <div className="space-y-2.5">
            {issues.map((issue, index) => (
              <article
                key={`${issue.category}-${issue.title}-${index}`}
                className={`rounded-lg border px-2.5 py-2 ${categoryStyles[issue.category] || categoryStyles.style}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-semibold text-gray-100">{issue.title}</h4>
                  <span className="text-[10px] uppercase tracking-[0.08em] opacity-75">
                    {categoryLabels[issue.category] || issue.category}
                  </span>
                </div>
                {issue.explanation && <p className="mt-1 text-xs leading-5 text-gray-300">{issue.explanation}</p>}
                {issue.suggestions?.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {issue.suggestions.slice(0, 3).map((suggestion) => (
                      <span key={suggestion} className="rounded-md bg-gray-950/35 px-2 py-1 text-[11px] text-gray-200">{suggestion}</span>
                    ))}
                  </div>
                )}
              </article>
            ))}
            {micro_tip && <p className="text-xs leading-5 text-sky-200"><strong>Dica:</strong> {micro_tip}</p>}
            {self_check_prompt && <p className="text-xs leading-5 text-gray-300"><strong>Confira:</strong> {self_check_prompt}</p>}
            {encouragement && <p className="text-xs leading-5 text-emerald-200">{encouragement}</p>}
          </div>
        </AnalysisDisclosure>
      )}

      {teacherAnalysis && (
        <AnalysisDisclosure
          title="Análise do professor"
          meta={`${teacherAnalysis.corrections?.length || 0} correções`}
        >
          <div className="space-y-3 text-xs leading-5">
            {teacherAnalysis.teacher_summary && <p className="text-gray-200">{teacherAnalysis.teacher_summary}</p>}
            {teacherAnalysis.corrections?.map((correction, index) => (
              <div key={`${correction.mistake}-${index}`} className="rounded-lg bg-gray-950/35 p-2.5">
                <p className="text-red-200"><span className="text-gray-500">Antes:</span> {correction.mistake}</p>
                <p className="text-emerald-200"><span className="text-gray-500">Melhor:</span> {correction.fix}</p>
                {correction.why && <p className="mt-1 text-gray-400">{correction.why}</p>}
              </div>
            ))}
            {teacherAnalysis.strengths?.length > 0 && <CompactList items={teacherAnalysis.strengths} tone="text-emerald-200" />}
            {teacherAnalysis.focus_areas?.length > 0 && <CompactList items={teacherAnalysis.focus_areas} tone="text-amber-200" />}
            {teacherAnalysis.next_practice?.length > 0 && <CompactList items={teacherAnalysis.next_practice} />}
            {teacherAnalysis.reflection_question && <p className="text-sky-200"><strong>Para refletir:</strong> {teacherAnalysis.reflection_question}</p>}
            {teacherAnalysis.encouragement && <p className="text-emerald-200">{teacherAnalysis.encouragement}</p>}
          </div>
        </AnalysisDisclosure>
      )}

      {studentProfile && (
        <AnalysisDisclosure title="Coach memory" meta={memoryMeta || 'perfil ativo'}>
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {cefrLevel && <span className="status-pill min-h-6 px-2 py-0.5 text-[10px]">CEFR {cefrLevel}</span>}
              {feedbackLanguage && <span className="status-pill min-h-6 px-2 py-0.5 text-[10px]">Feedback: {feedbackLanguage}</span>}
              {scaffoldingLevel && <span className="status-pill min-h-6 px-2 py-0.5 text-[10px]">Suporte: {humanize(scaffoldingLevel)}</span>}
            </div>
            {profileStrengths.length > 0 && <CompactList items={profileStrengths} tone="text-emerald-200" />}
            {profileWeaknesses.length > 0 && <CompactList items={profileWeaknesses} tone="text-amber-200" />}
            {recentTopics.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {recentTopics.map((recentTopic) => <span key={recentTopic} className="status-pill min-h-6 px-2 py-0.5 text-[10px]">{recentTopic}</span>)}
              </div>
            )}
            {metricSignals.length > 0 && (
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 border-t border-white/[0.07] pt-3 text-[11px]">
                {metricSignals.map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className="text-gray-500">{label}</dt>
                    <dd className="truncate text-gray-200">{humanize(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
            {metricCounts.length > 0 && (
              <dl className="grid grid-cols-3 gap-1.5">
                {metricCounts.map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-gray-950/35 p-2 text-center">
                    <dd className="text-sm font-semibold text-gray-100">{value}</dd>
                    <dt className="text-[9px] leading-3 text-gray-500">{label}</dt>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </AnalysisDisclosure>
      )}

      {lessonFrame && (lessonGoal || lessonFocus || lessonIntent || lessonMeta) && (
        <AnalysisDisclosure title="Foco da aula" meta={lessonMeta || 'em andamento'}>
          <dl className="space-y-2 text-xs leading-5">
            {lessonGoal && <div><dt className="text-gray-500">Objetivo</dt><dd className="text-gray-200">{lessonGoal}</dd></div>}
            {lessonFocus && <div><dt className="text-gray-500">Foco principal</dt><dd className="text-amber-200">{lessonFocus}</dd></div>}
            {lessonIntent && <div><dt className="text-gray-500">Intenção esperada</dt><dd className="text-sky-200">{humanize(lessonIntent)}</dd></div>}
            {stringValue(diagnostics, 'focus_origin') && (
              <div className="border-t border-white/[0.07] pt-2 text-[11px] text-gray-400">
                Origem do foco: {humanize(stringValue(diagnostics, 'focus_origin') || '')}
              </div>
            )}
          </dl>
        </AnalysisDisclosure>
      )}
    </section>
  );
};

export default AnalysisPanel;
