'use client';

import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface SkeletonCardProps {
  className?: string;
  rows?: number;
}

/**
 * Standardized SkeletonCard for AlphaForge bento-grid loading states.
 */
export function SkeletonCard({ className, rows = 3 }: SkeletonCardProps) {
  return (
    <div className={cn(
      "p-6 rounded-2xl border border-border-subtle bg-elevated/20 animate-pulse space-y-4",
      className
    )}>
      <div className="flex justify-between items-center mb-6">
        <Skeleton className="h-4 w-24 bg-border-subtle" />
        <Skeleton className="h-8 w-8 rounded-lg bg-border-subtle" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton 
            key={i} 
            className={cn(
              "h-12 w-full bg-border-subtle rounded-xl",
              i === rows - 1 && "w-2/3"
            )} 
          />
        ))}
      </div>
    </div>
  );
}
