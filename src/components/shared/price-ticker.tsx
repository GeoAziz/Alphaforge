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
      direction === 'up' && "bg-green/20 text-green border-green/30 shadow-[0_0_20px_rgba(52,211,153,0.2)] scale-[1.02]",
      direction === 'down' && "bg-red/20 text-red border-red/30 shadow-[0_0_20px_rgba(248,113,113,0.2)] scale-[0.98]",
      className
    )}>
      {prefix}<AnimatedCounter value={value} decimals={decimals} duration={400} />
    </div>
  );
}
