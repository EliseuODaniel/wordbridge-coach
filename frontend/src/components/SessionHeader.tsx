import AppBrand from './AppBrand';
import ModePicker from './ModePicker';
import type { TrainingMode } from './trainingModes';


interface SessionHeaderProps {
  activeMode: TrainingMode;
  title: string;
  description: string;
  onModeChange?: (mode: TrainingMode) => void;
  onExit?: () => void;
  actions?: React.ReactNode;
}


const SessionHeader = ({
  activeMode,
  title,
  description,
  onModeChange,
  onExit,
  actions,
}: SessionHeaderProps) => (
  <header className="sticky top-0 z-30 border-b border-white/[0.07] bg-gray-900/80 backdrop-blur-2xl">
    <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3 sm:px-6 lg:flex-nowrap lg:px-8">
      <AppBrand compact className="mr-auto" />
      <div className="order-3 min-w-0 basis-full lg:order-none lg:mr-auto lg:basis-auto">
        <h1 className="truncate text-base font-semibold tracking-[-0.02em] text-white">{title}</h1>
        <p className="truncate text-xs text-gray-400">{description}</p>
      </div>
      {onModeChange && (
        <div className="order-4 w-full overflow-x-auto lg:order-none lg:w-auto">
          <ModePicker selectedMode={activeMode} onModeSelect={onModeChange} compact />
        </div>
      )}
      <div className="ml-auto flex items-center gap-2 lg:ml-0">
        {actions}
        {onExit && (
          <button type="button" onClick={onExit} className="btn btn-secondary min-h-10 px-3 text-xs">
            Perfis
          </button>
        )}
      </div>
    </div>
  </header>
);


export default SessionHeader;
