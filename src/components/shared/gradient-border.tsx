
'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GradientBorderProps {
  children: ReactNode;
  className?: string;
  active?: boolean;
}

export function GradientBorder({ children, className, active = false }: GradientBorderProps) {
  return (
    <div className={cn(
      "relative p-[1px] rounded-2xl overflow-hidden group",
      active ? "bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-xy" : "bg-border-subtle",
      className
    )}>
      <div className="relative bg-surface rounded-[calc(1rem-1px)] h-full w-full">
        {children}
      </div>
    </div>
  );
}
