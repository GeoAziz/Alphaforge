'use client';

import { cn } from '@/lib/utils';
import { SpotlightCard } from './spotlight-card';
import { AnimatedCounter } from './animated-counter';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface StatCardProps {
  label: string;
  value: number | string;
  change?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  isHero?: boolean;
  loading?: boolean;
  className?: string;
}

/**
 * StatCard - High-density metric display for AlphaForge terminal nodes.
 * Features hero modes with gradient text and directional performance indicators.
 */
export function StatCard({
  label,
  value,
  change,
  prefix = '',
  suffix = '',
  decimals = 0,
  isHero = false,
  loading = false,
  className
}: StatCardProps) {
  if (loading) {
    return (
      <SpotlightCard className={cn("p-6 space-y-4", className)}>
        <Skeleton className="h-3 w-20 bg-border-subtle" />
        <Skeleton className="h-8 w-full bg-border-subtle" />
        <Skeleton className="h-3 w-24 bg-border-subtle" />
      </SpotlightCard>
    );
  }

  const isNumericValue = typeof value === 'number';
  const showChange = change !== undefined;

  return (
    <SpotlightCard 
      variant={isHero ? 'accent' : 'default'}
      className={cn(
        "p-6 flex flex-col justify-between group transition-all",
        isHero && "bg-primary/5 border-primary/20",
        className
      )}
    >
      <div className="space-y-1">
        <div className="text-[10px] font-black uppercase tracking-widest text-text-muted group-hover:text-text-secondary transition-colors">
          {label}
        </div>
        <div className={cn(
          "font-mono font-black tracking-tighter",
          isHero ? "text-3xl lg:text-4xl gradient-text" : "text-2xl text-text-primary"
        )}>
          {isNumericValue ? (
            <AnimatedCounter 
              value={value as number} 
              prefix={prefix} 
              suffix={suffix} 
              decimals={decimals} 
            />
          ) : (
            <span>{value}</span>
          )}
        </div>
      </div>

      {showChange && (
        <div className="mt-4 flex items-center gap-2">
          <div className={cn(
            "flex items-center gap-1 text-[10px] font-black uppercase tracking-widest",
            change > 0 ? "text-green" : change < 0 ? "text-red" : "text-text-muted"
          )}>
            {change > 0 ? <TrendingUp size={12} /> : change < 0 ? <TrendingDown size={12} /> : <Minus size={12} />}
            {change > 0 ? '+' : ''}{change}%
          </div>
          <span className="text-[9px] font-bold text-text-muted uppercase">vs 24h cluster</span>
        </div>
      )}
    </SpotlightCard>
  );
}
