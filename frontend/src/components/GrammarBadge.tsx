/** Grammar Badge Component */

import React from 'react';

interface GrammarBadgeProps {
  grammarHint: string;
  className?: string;
}

const GrammarBadge: React.FC<GrammarBadgeProps> = ({ grammarHint, className = '' }) => {
  return (
    <div className={`status-pill min-h-7 px-2.5 py-1 text-[11px] ${className}`}>
      {grammarHint}
    </div>
  );
};

export default GrammarBadge;
