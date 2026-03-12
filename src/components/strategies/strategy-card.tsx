'use client';

import { Strategy } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { TrendingUp, Info, Share2 } from 'lucide-react';

interface StrategyCardProps {
  strategy: Strategy;
  onSelect?: (strategy: Strategy) => void;
  isSelected?: boolean;
}

/**
 * StrategyCard - Institutional strategy overview card.
 * Displays key metrics, risk level, and status.
 */
export function StrategyCard({ strategy, onSelect, isSelected }: StrategyCardProps) {
  const riskColors = {
    Low: 'bg-green/10 text-green border-green/20',
    Medium: 'bg-amber/10 text-amber border-amber/20',
    High: 'bg-red/10 text-red border-red/20',
  };

  return (
    <SpotlightCard
      onClick={() => onSelect?.(strategy)}
      className={cn(
        'p-6 lg:p-8 cursor-pointer transition-all group',
        isSelected && 'border-primary ring-1 ring-primary/20'
      )}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-black tracking-tighter uppercase text-text-primary group-hover:text-primary transition-colors line-clamp-2 leading-none">
                {strategy.name}
              </h3>
            </div>
            <Badge variant="outline" className="text-[9px] font-black uppercase border-text-muted/20 text-text-muted h-6 px-2 shrink-0">
              {strategy.status}
            </Badge>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed font-medium uppercase line-clamp-2 max-h-[40px]">
            {strategy.description}
          </p>
        </div>

        <div className="h-px bg-border-subtle" />

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-[8px] font-black uppercase text-text-muted tracking-widest">Win Rate</div>
            <div className="text-lg font-black text-green">{strategy.winRate.toFixed(1)}%</div>
          </div>
          <div className="space-y-1">
            <div className="text-[8px] font-black uppercase text-text-muted tracking-widest">Avg ROI</div>
            <div className="text-lg font-black text-primary">+{strategy.avgRoi.toFixed(1)}%</div>
          </div>
          <div className="space-y-1">
            <div className="text-[8px] font-black uppercase text-text-muted tracking-widest">Sharpe</div>
            <div className="text-lg font-black text-text-primary">{strategy.sharpeRatio?.toFixed(2) || '—'}</div>
          </div>
          <div className="space-y-1">
            <div className="text-[8px] font-black uppercase text-text-muted tracking-widest">Max DD</div>
            <div className="text-lg font-black text-red">{strategy.maxDrawdown?.toFixed(1) || '—'}%</div>
          </div>
        </div>

        <div className="h-px bg-border-subtle" />

        {/* Risk & Status */}
        <div className="flex items-center justify-between gap-4">
          <Badge className={cn('font-black uppercase text-[10px] h-7 px-3', riskColors[strategy.riskLevel as keyof typeof riskColors] || 'bg-elevated border-border-subtle')}>
            {strategy.riskLevel} Risk
          </Badge>

          <div className="text-[8px] font-black text-text-muted uppercase tracking-widest">
            {strategy.signals ? `${strategy.signals} Signals` : 'No Signals'}
          </div>
        </div>

        {/* CTA */}
        <Button
          onClick={(e) => {
            e.stopPropagation();
            onSelect?.(strategy);
          }}
          className="w-full h-10 bg-primary text-primary-foreground font-black uppercase text-[10px] gap-2 rounded-xl group-hover:scale-[1.02] transition-transform"
        >
          <TrendingUp size={14} />
          View Details
        </Button>
      </div>
    </SpotlightCard>
  );
}
