import React from 'react';


interface AppBrandProps {
  compact?: boolean;
  className?: string;
}


const AppBrand: React.FC<AppBrandProps> = ({ compact = false, className = '' }) => (
  <div className={`inline-flex items-center gap-3 ${className}`}>
    <span className={`${compact ? 'size-10 rounded-xl' : 'size-12 rounded-2xl'} relative inline-flex shrink-0 items-center justify-center overflow-hidden bg-primary-500 shadow-glow`}>
      <svg viewBox="0 0 48 48" className="size-8" fill="none" aria-hidden="true">
        <path d="M7 29c4-8 10-12 17-12s13 4 17 12" stroke="white" strokeWidth="3.8" strokeLinecap="round" />
        <path d="M12 29v7m24-7v7M24 17v19" stroke="#BFF8EF" strokeWidth="3" strokeLinecap="round" />
        <path d="M7 36h34" stroke="white" strokeWidth="3.8" strokeLinecap="round" />
      </svg>
    </span>
    <span className="min-w-0 text-left">
      <span className={`${compact ? 'text-base' : 'text-lg'} block truncate font-semibold tracking-[-0.025em] text-white`}>
        WordBridge
      </span>
      <span className="block text-[10px] font-semibold uppercase tracking-[0.22em] text-gray-400">
        language coach
      </span>
    </span>
  </div>
);


export default AppBrand;
