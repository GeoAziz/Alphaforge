'use client';

import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface SkeletonCardProps {
  className?: string;
  rows?: number;
}

/**
 * Standardized SkeletonCard for AlphaForge bento-grid loading states.
 * Uses consistent institutional shimmer animation.
 */
export function SkeletonCard({ className, rows = 3 }: SkeletonCardProps) {
  return (
    <div className={cn(
      "p-6 rounded-2xl border border-border-subtle bg-elevated/20 space-y-4 animate-skeleton overflow-hidden",
      className
    )}>
      <div className="flex justify-between items-center mb-6">
        <Skeleton className="h-4 w-24 bg-border-subtle/50" />
        <Skeleton className="h-8 w-8 rounded-lg bg-border-subtle/50" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton 
            key={i} 
            className={cn(
              "h-12 w-full bg-border-subtle/30 rounded-xl",
              i === rows - 1 && "w-2/3"
            )} 
          />
        ))}
      </div>
    </div>
  );
}
