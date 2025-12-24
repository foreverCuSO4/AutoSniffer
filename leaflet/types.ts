import React from 'react';

// Fix: Added React import to resolve namespace issues for React.ReactNode
export interface PanelProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export enum ViewMode {
  INSIDE = 'INSIDE',
  OUTSIDE = 'OUTSIDE'
}