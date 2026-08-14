import ModeGlyph from './ModeGlyph';
import InfoTooltip from './InfoTooltip';
import { TRAINING_MODES, type TrainingMode } from './trainingModes';


interface ModePickerProps {
  selectedMode: TrainingMode;
  onModeSelect: (mode: TrainingMode) => void;
  compact?: boolean;
}


const ModePicker = ({ selectedMode, onModeSelect, compact = false }: ModePickerProps) => (
  <div
    className={compact
      ? 'inline-flex rounded-2xl border border-white/10 bg-gray-950/45 p-1'
      : 'grid grid-cols-3 gap-2 sm:gap-3'}
    role="radiogroup"
    aria-label="Modo de estudo"
  >
    {TRAINING_MODES.map((mode) => {
      const active = selectedMode === mode.id;
      return (
        <span key={mode.id} className={compact ? '' : 'relative block'}>
          <button
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onModeSelect(mode.id)}
            title={compact ? mode.description : undefined}
            className={compact
              ? `inline-flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold transition ${active ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:bg-white/[0.05] hover:text-gray-200'}`
              : `flex min-h-[72px] w-full flex-col items-center justify-center gap-1.5 rounded-2xl border px-2 py-2.5 text-center transition duration-200 sm:min-h-[68px] sm:flex-row sm:justify-start sm:gap-3 sm:p-3 sm:pr-10 sm:text-left ${active ? 'border-primary-400/55 bg-primary-500/10 shadow-glow' : 'border-white/[0.08] bg-white/[0.025] hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.05]'}`}
            data-testid={`mode-picker-${mode.id}`}
          >
            <span className={compact
              ? `inline-flex size-7 items-center justify-center rounded-lg ${active ? 'bg-primary-400/20 text-primary-200' : 'text-gray-500'}`
              : `inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${mode.accent} text-white shadow-lg`}>
              <ModeGlyph mode={mode.id} className={compact ? 'size-4' : 'size-5'} />
            </span>
            <span className={compact ? '' : 'block text-xs font-semibold text-white sm:text-sm'}>
              {compact ? mode.shortLabel : (
                <><span className="sm:hidden">{mode.shortLabel}</span><span className="hidden sm:inline">{mode.label}</span></>
              )}
            </span>
          </button>
          {!compact && (
            <span className="absolute right-1 top-1 sm:right-2 sm:top-1/2 sm:-translate-y-1/2">
              <InfoTooltip label={`Sobre ${mode.label}`}><strong className="mb-1 block text-white">{mode.label}</strong>{mode.description}</InfoTooltip>
            </span>
          )}
        </span>
      );
    })}
  </div>
);


export default ModePicker;
