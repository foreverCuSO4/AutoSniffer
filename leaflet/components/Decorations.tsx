
import React from 'react';

export const OrnateCorner = ({ className = "" }) => (
  <svg className={`absolute ${className}`} width="120" height="120" viewBox="0 0 120 120" fill="none">
    <path d="M10 10 Q 40 10, 40 40 M10 10 Q 10 40, 40 40 M10 10 L 100 10 M10 10 L 10 100" stroke="#c5a059" strokeWidth="0.5" strokeOpacity="0.5" />
    <circle cx="40" cy="40" r="2" fill="#c5a059" fillOpacity="0.4" />
    <path d="M10 10 L 25 25" stroke="#c5a059" strokeWidth="0.5" strokeOpacity="0.3" />
  </svg>
);

export const TechnicalFiligree = ({ className = "" }) => (
  <svg className={`absolute opacity-10 pointer-events-none ${className}`} width="200" height="200" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="0.2" fill="none" />
    <circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="0.1" fill="none" strokeDasharray="1 2" />
    <path d="M50 5 L 50 15 M95 50 L 85 50 M50 95 L 50 85 M5 50 L 15 50" stroke="currentColor" strokeWidth="0.5" />
    <path d="M10 10 Q 50 50 90 90 M90 10 Q 50 50 10 90" stroke="currentColor" strokeWidth="0.1" />
  </svg>
);

export const OrnateDivider = () => (
  <div className="flex items-center justify-center gap-6 my-8 opacity-60">
    <div className="h-[0.5px] w-20 bg-gradient-to-r from-transparent to-[#c5a059]"></div>
    <div className="relative">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="gear-spin">
        <path d="M12 2L14.5 9H21.5L16 13L18.5 20L12 16L5.5 20L8 13L2.5 9H9.5L12 2Z" stroke="#c5a059" strokeWidth="1" />
      </svg>
    </div>
    <div className="h-[0.5px] w-20 bg-gradient-to-l from-transparent to-[#c5a059]"></div>
  </div>
);

export const FloatingParticle = ({ style }: { style: React.CSSProperties }) => (
  <div 
    className="absolute pointer-events-none opacity-10 floating"
    style={{
      width: '12px',
      height: '12px',
      border: '0.5px solid #c5a059',
      borderRadius: '2px',
      transform: 'rotate(45deg)',
      ...style
    }}
  />
);
