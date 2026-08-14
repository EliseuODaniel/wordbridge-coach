import type { TrainingMode } from './trainingModes';


interface ModeGlyphProps {
  mode: TrainingMode;
  className?: string;
}


const ModeGlyph = ({ mode, className = 'size-5' }: ModeGlyphProps) => {
  if (mode === 'lingvist') {
    return (
      <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 19.5h16M6.5 16l1.2-4.8L16.8 2a1.5 1.5 0 0 1 2.1 0l1.1 1.1a1.5 1.5 0 0 1 0 2.1l-9.2 9.1L6.5 16Z" />
      </svg>
    );
  }
  if (mode === 'chat') {
    return (
      <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M7 18.5 3.5 21v-5.2A8.2 8.2 0 0 1 2 11c0-5 4.5-9 10-9s10 4 10 9-4.5 9-10 9a11 11 0 0 1-5-.5Z" />
        <path strokeLinecap="round" d="M7.5 10.5h9M7.5 14h5.5" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <path strokeLinecap="round" d="m15.5 8.5 4-4m0 0v3.4m0-3.4h-3.4" />
    </svg>
  );
};


export default ModeGlyph;
