import React from 'react';

interface AnalysisDisclosureProps {
  children: React.ReactNode;
  meta?: string | null;
  title: string;
}

const AnalysisDisclosure: React.FC<AnalysisDisclosureProps> = ({
  children,
  meta,
  title,
}) => (
  <details className="group overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.025] open:bg-white/[0.04]">
    <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2.5 text-left [&::-webkit-details-marker]:hidden">
      <span className="min-w-0 flex-1 truncate text-xs font-semibold text-gray-200">{title}</span>
      {meta && (
        <span className="max-w-40 truncate text-[10px] font-medium uppercase tracking-[0.08em] text-gray-500">
          {meta}
        </span>
      )}
      <svg
        viewBox="0 0 20 20"
        className="size-4 shrink-0 text-gray-500 transition group-open:rotate-180"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="m6 8 4 4 4-4" />
      </svg>
    </summary>
    <div className="border-t border-white/[0.07] px-3 py-3">{children}</div>
  </details>
);

export default AnalysisDisclosure;
