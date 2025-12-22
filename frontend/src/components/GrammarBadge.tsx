/** Grammar Badge Component */

import React from 'react';

interface GrammarBadgeProps {
  grammarHint: string;
  className?: string;
}

const GrammarBadge: React.FC<GrammarBadgeProps> = ({ grammarHint, className = '' }) => {
  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-700 text-gray-200 border border-gray-600 ${className}`}>
      {grammarHint}
    </div>
  );
};

export default GrammarBadge;