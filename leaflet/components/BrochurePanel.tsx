
import React from 'react';
import { PanelProps } from '../types';
import { OrnateCorner } from './Decorations';

const BrochurePanel: React.FC<PanelProps> = ({ children, className = "", id }) => {
  return (
    <div 
      id={id}
      className={`flex-1 min-w-[320px] max-w-[400px] h-[720px] glass rounded-3xl p-8 flex flex-col shadow-2xl relative overflow-hidden transition-all duration-500 hover:shadow-amber-900/10 border-2 border-amber-100/50 ${className}`}
    >
      {/* Ornate corners */}
      <OrnateCorner className="top-2 left-2" />
      <OrnateCorner className="top-2 right-2 rotate-90" />
      <OrnateCorner className="bottom-2 left-2 -rotate-90" />
      <OrnateCorner className="bottom-2 right-2 rotate-180" />
      
      {/* Content wrapper with inner padding for ornate border look */}
      <div className="relative z-10 flex flex-col h-full">
        {children}
      </div>

      {/* Decorative center backdrop */}
      <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
        <svg width="400" height="400" viewBox="0 0 100 100" fill="currentColor" className="text-amber-900">
          <path d="M50 0 C 60 40 100 50 60 60 C 50 100 40 60 0 50 C 40 40 50 0" />
        </svg>
      </div>
    </div>
  );
};

export default BrochurePanel;
