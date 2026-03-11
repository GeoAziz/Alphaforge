'use client';

import { useMockRealtime } from '@/hooks/use-mock-realtime';
import { cn } from '@/lib/utils';
import { AnimatedCounter } from './animated-counter';

interface PriceTickerProps {
  initialPrice: number;
  decimals?: number;
  prefix?: string;
  className?: string;
}

/**
 * PriceTicker displays a live-jittered price with directional flash animations.
 * Institutional grade green/red directional signaling on value change.
 */
export function PriceTicker({ initialPrice, decimals = 2, prefix = '$', className }: PriceTickerProps) {
  const { value, direction } = useMockRealtime(initialPrice);

  return (
    <div className={cn(
      "transition-all duration-300 rounded px-1.5 py-0.5 -mx-1.5 font-mono font-bold inline-block border border-transparent",
      direction === 'up' && "animate-price-up text-green scale-[1.02]",
      direction === 'down' && "animate-price-down text-red scale-[0.98]",
      className
    )}>
      {prefix}<AnimatedCounter value={value} decimals={decimals} duration={400} />
    </div>
  );
}