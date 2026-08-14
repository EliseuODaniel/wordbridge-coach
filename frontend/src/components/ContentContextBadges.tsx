import type { ContentContext } from '../services/apiCards';


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
    <div className="flex flex-wrap gap-2" aria-label="Contexto do conteúdo">
      {labels.map((label) => (
        <span key={label} className="px-2.5 py-1 bg-gray-800 border border-gray-700 text-gray-400 text-xs rounded">
          {label}
        </span>
      ))}
      {context.license_name && (
        <span className="px-2.5 py-1 bg-gray-800 border border-gray-700 text-gray-500 text-xs rounded">
          {context.license_name}
        </span>
      )}
    </div>
  );
};


export default ContentContextBadges;
