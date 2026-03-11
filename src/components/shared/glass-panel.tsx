'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'accent';
}

/**
 * GlassPanel provides the signature AlphaForge semi-transparent,
 * blurred surface for terminal modules.
 */
export function GlassPanel({ children, className, variant = 'default' }: GlassPanelProps) {
  return (
    <div className={cn(
      "glass rounded-2xl overflow-hidden transition-all duration-300",
      variant === 'elevated' && "bg-elevated/40 border-primary/10 shadow-2xl",
      variant === 'accent' && "bg-primary/5 border-primary/20 shadow-[0_0_30px_rgba(96,165,250,0.05)]",
      className
    )}>
      {children}
    </div>
  );
}
