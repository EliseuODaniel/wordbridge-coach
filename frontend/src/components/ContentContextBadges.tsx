import type { ContentContext } from '../services/apiCards';
import InfoTooltip from './InfoTooltip';


interface ContentContextBadgesProps {
  context?: ContentContext | null;
}


const ContentContextBadges = ({ context }: ContentContextBadgesProps) => {
  if (!context) return null;

  const labels = [
    context.cefr_level ? `Faixa ${context.cefr_level}` : null,
    context.domain ?? null,
    context.register ?? null,
    context.is_contemporary ? 'inglês contemporâneo' : null,
  ].filter((label): label is string => Boolean(label));

  return (
    <div className="flex min-h-11 flex-wrap items-center gap-1.5 rounded-2xl border border-white/[0.07] bg-white/[0.025] px-3 py-2" aria-label="Contexto do conteúdo">
      {labels.map((label) => (
        <span key={label} className="status-pill min-h-6 px-2 py-0.5 text-[11px]">
          {label}
        </span>
      ))}
      <span className="ml-auto" />
      <InfoTooltip label="Proveniência do conteúdo">
        <strong className="mb-1 block text-white">Conteúdo revisado</strong>
        <span className="block">Qualidade: {context.quality_status}. Versão: {context.content_version}.</span>
        {context.license_name && <span className="mt-1 block text-gray-400">Licença: {context.license_name}</span>}
      </InfoTooltip>
    </div>
  );
};


export default ContentContextBadges;
