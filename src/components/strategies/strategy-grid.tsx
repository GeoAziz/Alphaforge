'use client';

import { Strategy } from '@/lib/types';
import { StrategyCard } from './strategy-card';

interface StrategyGridProps {
  strategies: Strategy[];
  onSelectStrategy: (strategy: Strategy) => void;
  selectedId?: string;
  isLoading?: boolean;
}

/**
 * StrategyGrid - Responsive 3-column grid for strategy cards.
 */
export function StrategyGrid({ strategies, onSelectStrategy, selectedId, isLoading }: StrategyGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
        {Array(6)
          .fill(0)
          .map((_, i) => (
            <div key={i} className="h-80 rounded-3xl bg-elevated/20 animate-pulse border border-border-subtle" />
          ))}
      </div>
    );
  }

  if (strategies.length === 0) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">No strategies available</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
      {strategies.map(strategy => (
        <StrategyCard
          key={strategy.id}
          strategy={strategy}
          onSelect={onSelectStrategy}
          isSelected={strategy.id === selectedId}
        />
      ))}
    </div>
  );
}
