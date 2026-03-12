'use client';

import { MarketplaceStrategy } from '@/lib/types';
import { MarketplaceCard } from './marketplace-card';

interface MarketplaceGridProps {
  strategies: MarketplaceStrategy[];
  onSubscribe: (strategy: MarketplaceStrategy) => void;
  subscribingId: string | null;
  isLoading: boolean;
}

/**
 * MarketplaceGrid - 12-column responsive grid layout for strategy nodes.
 */
export function MarketplaceGrid({ strategies, onSubscribe, subscribingId, isLoading }: MarketplaceGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        {Array(4).fill(0).map((_, i) => (
          <div key={i} className="h-[500px] rounded-3xl bg-elevated/20 animate-pulse border border-border-subtle" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
      {strategies.map((strategy) => (
        <MarketplaceCard 
          key={strategy.id} 
          strategy={strategy} 
          onSubscribe={onSubscribe}
          isSubscribing={subscribingId === strategy.id}
        />
      ))}
    </div>
  );
}
