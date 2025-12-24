
import React from 'react';

export const FolderIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

export const RobotIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
  </svg>
);

export const MagicWandIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a2 2 0 00-1.96 1.414l-.477 2.387a2 2 0 00.547 1.022l1.428 1.428a2 2 0 001.022.547l2.387.477a2 2 0 001.96-1.414l.477-2.387a2 2 0 00-.547-1.022l-1.428-1.428z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 3h6v6" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 3l-7 7" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l-7 7" />
  </svg>
);

export const UndoIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
  </svg>
);

export const Logo = ({ className = "w-16 h-16" }) => (
  <div className={`relative flex items-center justify-center rounded-2xl bg-amber-100 p-2 shadow-inner border border-amber-200 ${className}`}>
    <FolderIcon className="w-10 h-10 text-amber-700 opacity-30 absolute" />
    <RobotIcon className="w-8 h-8 text-amber-800 relative z-10" />
    <div className="absolute top-1 right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
  </div>
);
