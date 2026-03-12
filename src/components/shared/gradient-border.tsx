'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GradientBorderProps {
  children: ReactNode;
  className?: string;
  active?: boolean;
}

/**
 * GradientBorder implements the high-confidence signal glow.
 * When active (≥85% confidence), it applies an animated multi-stop gradient border.
 * Features rotating technical conic-style sweep simulation.
 */
export function GradientBorder({ children, className, active = false }: GradientBorderProps) {
  return (
    <div className={cn(
      "relative p-[1.5px] rounded-2xl overflow-hidden group transition-all duration-700",
      active 
        ? "bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-xy shadow-[0_0_30px_rgba(96,165,250,0.25)]" 
        : "bg-border-subtle",
      className
    )}>
      <div className="relative bg-surface rounded-[calc(1rem-1.5px)] h-full w-full overflow-hidden">
        {children}
      </div>
      {active && (
        <div className="absolute inset-0 pointer-events-none opacity-20 bg-gradient-to-r from-primary via-accent to-primary animate-terminal-pulse blur-2xl -z-10" />
      )}
    </div>
  );
}
