import type { CompetencyContext } from '../services/apiCards';
import InfoTooltip from './InfoTooltip';


interface CompetencyPanelProps {
  competency?: CompetencyContext | null;
}


const CompetencyPanel = ({ competency }: CompetencyPanelProps) => {
  if (!competency) return null;

  return (
    <section className="surface-soft flex items-center gap-3 p-3" aria-label="Competência praticada">
      <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary-400/10 text-primary-200">
        <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="m12 3 2.1 4.3 4.7.7-3.4 3.3.8 4.7-4.2-2.2L7.8 16l.8-4.7L5.2 8l4.7-.7L12 3Z" />
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-500">Competência {competency.framework_level}</div>
        <div className="truncate text-sm font-semibold text-gray-100">{competency.name}</div>
      </div>
      <span className="whitespace-nowrap text-sm font-semibold tabular-nums text-primary-200">{Math.round(competency.mastery_probability * 100)}%</span>
      <InfoTooltip label="Detalhes da competência">
        <strong className="mb-1 block text-white">{competency.name}</strong>
        <span className="block">{competency.can_do_descriptor}</span>
        <span className="mt-2 block text-gray-400">{competency.observation_count} observações · {Math.round(competency.confidence * 100)}% de confiança.</span>
        <span className="mt-2 block text-gray-500">Estimativa instrucional; não equivale a certificação CEFR.</span>
      </InfoTooltip>
    </section>
  );
};


export default CompetencyPanel;
