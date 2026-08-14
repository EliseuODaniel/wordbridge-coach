import type { CompetencyContext } from '../services/apiCards';


interface CompetencyPanelProps {
  competency?: CompetencyContext | null;
}


const CompetencyPanel = ({ competency }: CompetencyPanelProps) => {
  if (!competency) return null;

  return (
    <section className="bg-gray-800 rounded-lg p-4 border border-indigo-800" aria-label="Competência praticada">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-xs uppercase tracking-wide text-indigo-300">
            Competência {competency.framework_level}
          </div>
          <div className="font-semibold text-gray-100">{competency.name}</div>
          <div className="text-sm text-gray-400 mt-1">{competency.can_do_descriptor}</div>
        </div>
        <div className="text-right text-xs text-gray-400">
          <div>{Math.round(competency.mastery_probability * 100)}% de domínio estimado</div>
          <div>{competency.observation_count} observações</div>
          <div>{Math.round(competency.confidence * 100)}% de confiança na estimativa</div>
        </div>
      </div>
      <div className="text-[11px] text-gray-500 mt-3">
        Estimativa instrucional baseada nas atividades do app; não equivale a certificação CEFR.
      </div>
    </section>
  );
};


export default CompetencyPanel;
