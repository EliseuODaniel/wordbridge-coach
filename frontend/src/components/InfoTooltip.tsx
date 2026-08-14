import { useId } from 'react';


interface InfoTooltipProps {
  label: string;
  children: React.ReactNode;
  align?: 'left' | 'right';
}


const InfoTooltip = ({ label, children, align = 'right' }: InfoTooltipProps) => {
  const tooltipId = useId();

  return (
    <span className="group/tooltip relative inline-flex shrink-0">
      <button
        type="button"
        aria-label={label}
        aria-describedby={tooltipId}
        className="inline-flex size-7 min-h-7 min-w-7 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-[11px] font-bold text-gray-400 transition hover:border-primary-300/40 hover:bg-primary-400/10 hover:text-primary-200"
      >
        i
      </button>
      <span
        id={tooltipId}
        role="tooltip"
        className={`pointer-events-none invisible absolute top-[calc(100%+0.55rem)] z-50 w-72 translate-y-1 rounded-xl border border-white/10 bg-gray-950/95 p-3 text-left text-xs font-normal leading-5 text-gray-300 opacity-0 shadow-panel backdrop-blur-xl transition group-hover/tooltip:visible group-hover/tooltip:translate-y-0 group-hover/tooltip:opacity-100 group-focus-within/tooltip:visible group-focus-within/tooltip:translate-y-0 group-focus-within/tooltip:opacity-100 ${align === 'left' ? 'left-0' : 'right-0'}`}
      >
        {children}
      </span>
    </span>
  );
};


export default InfoTooltip;
