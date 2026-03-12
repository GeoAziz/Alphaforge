
'use client';

import { BacktestResult } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { TrendingUp, Zap, ShieldAlert, BarChart3 } from 'lucide-react';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { cn } from '@/lib/utils';

interface BacktestResultsProps {
  results: BacktestResult;
}

export function BacktestResults({ results }: BacktestResultsProps) {
  const stats = [
    { label: 'Simulated ROI', value: results.roi, prefix: '+', suffix: '%', icon: TrendingUp, color: 'text-green', bg: 'bg-green/10' },
    { label: 'Win Efficiency', value: results.winRate, suffix: '%', icon: Zap, color: 'text-primary', bg: 'bg-primary/10' },
    { label: 'Sharpe Ratio', value: results.sharpeRatio, icon: BarChart3, color: 'text-accent', bg: 'bg-accent/10' },
    { label: 'Max Drawdown', value: results.maxDrawdown, suffix: '%', icon: ShieldAlert, color: 'text-red', bg: 'bg-red/10' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {stats.map((stat, i) => (
        <SpotlightCard key={stat.label} className="p-6 border-border-subtle hover:border-primary/20 transition-all">
          <div className="flex items-center justify-between mb-4">
            <div className={cn("p-2 rounded-lg", stat.bg, stat.color)}>
              <stat.icon size={16} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest text-text-muted">{stat.label}</span>
          </div>
          <div className={cn("text-3xl font-black font-mono tracking-tighter", stat.color)}>
            <AnimatedCounter value={stat.value} prefix={stat.prefix} suffix={stat.suffix} decimals={stat.value % 1 !== 0 ? 2 : 0} />
          </div>
          <div className="mt-2 text-[8px] font-bold text-text-muted uppercase tracking-tighter">
            Resolved over {results.totalTrades} nodes
          </div>
        </SpotlightCard>
      ))}
    </div>
  );
}
