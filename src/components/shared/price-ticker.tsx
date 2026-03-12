'use client';

import { useMockRealtime } from '@/hooks/use-mock-realtime';
import { cn } from '@/lib/utils';
import { AnimatedCounter } from './animated-counter';

interface PriceTickerProps {
  initialPrice: number;
  decimals?: number;
  prefix?: string;
  className?: string;
  showFlash?: boolean;
}

/**
 * PriceTicker displays a live-jittered price with directional flash animations.
 * 
 * Accessibility:
 * - aria-live="polite" ensures price updates are announced reasonably.
 * - sr-only spans provide directional cues for non-visual users.
 */
export function PriceTicker({ 
  initialPrice, 
  decimals = 2, 
  prefix = '$', 
  className,
  showFlash = true 
}: PriceTickerProps) {
  const { value, direction } = useMockRealtime(initialPrice);

  return (
    <div 
      className={cn(
        "transition-all duration-300 rounded-md px-2 py-1 font-mono font-bold inline-block border border-transparent min-w-[100px]",
        showFlash && direction === 'up' && "animate-price-up text-green",
        showFlash && direction === 'down' && "animate-price-down text-red",
        className
      )}
      aria-live="polite"
      role="status"
    >
      <span className="sr-only">
        {direction === 'up' ? 'Price Up: ' : direction === 'down' ? 'Price Down: ' : 'Current Price: '}
      </span>
      {prefix}<AnimatedCounter value={value} decimals={decimals} duration={400} />
    </div>
  );
}
