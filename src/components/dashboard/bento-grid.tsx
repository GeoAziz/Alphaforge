'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface BentoCellProps {
  children: ReactNode;
  className?: string;
  cols?: 1 | 2 | 3 | 4 | 6 | 8;
  rows?: 1 | 2 | 3;
}

export function BentoCell({ children, className, cols = 4, rows = 1 }: BentoCellProps) {
  const colSpanClass = {
    1: 'col-span-1',
    2: 'col-span-2',
    3: 'col-span-3',
    4: 'col-span-4',
    6: 'col-span-6',
    8: 'col-span-8',
  }[cols];

  const rowSpanClass = {
    1: 'row-span-1',
    2: 'row-span-2',
    3: 'row-span-3',
  }[rows];

  return (
    <div className={cn(
      'rounded-2xl border border-border overflow-hidden',
      colSpanClass,
      rowSpanClass,
      className
    )}>
      {children}
    </div>
  );
}

interface BentoGridProps {
  children: ReactNode;
  className?: string;
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div className={cn(
      'grid grid-cols-12 auto-rows-[300px] gap-4',
      'lg:gap-6',
      className
    )}>
      {children}
    </div>
  );
}
