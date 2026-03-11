
'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { PortfolioSummary } from '@/lib/types';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Zap, BarChart3, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PerformanceSummaryProps {
  summary?: PortfolioSummary | null;
  isLoading?: boolean;
}

export function PerformanceSummary({ summary, isLoading }: PerformanceSummaryProps) {
  const stats = [
    {
      label: 'Session Alpha',
      value: summary?.unrealizedPnl || 0,
      prefix: (summary?.unrealizedPnl || 0) >= 0 ? '+$' : '-$',
      icon: TrendingUp,
      color: (summary?.unrealizedPnl || 0) >= 0 ? 'text-green' : 'text-red',
      bg: (summary?.unrealizedPnl || 0) >= 0 ? 'bg-green/10' : 'bg-red/10',
      description: 'Aggregate unrealized PnL'
    },
    {
      label: 'Profit Factor',
      value: 2.15,
      icon: Zap,
      color: 'text-primary',
      bg: 'bg-primary/10',
      description: 'Institutional grade yield'
    },
    {
      label: 'Risk Exposure',
      value: summary?.marginUsed || 0,
      suffix: '%',
      icon: AlertTriangle,
      color: 'text-amber',
      bg: 'bg-amber/10',
      description: 'Active margin utilization'
    },
    {
      label: 'Total Clusters',
      value: summary?.totalTrades || 0,
      icon: BarChart3,
      color: 'text-text-primary',
      bg: 'bg-elevated',
      description: 'Resolved data signals'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-full">
      {stats.map((stat, i) => (
        <SpotlightCard key={i} className="p-6 flex flex-col justify-between group">
          <div className="flex items-center justify-between mb-4">
            <div className={cn("p-2 rounded-lg transition-transform group-hover:scale-110", stat.bg, stat.color)}>
              <stat.icon size={18} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest text-text-muted">{stat.label}</span>
          </div>
          <div className="space-y-1">
            <div className={cn("text-2xl font-black font-mono tracking-tighter", stat.color)}>
              {isLoading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <AnimatedCounter 
                  value={Math.abs(stat.value)} 
                  prefix={stat.prefix} 
                  suffix={stat.suffix} 
                  decimals={stat.value % 1 !== 0 ? 2 : 0} 
                />
              )}
            </div>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-tight">{stat.description}</p>
          </div>
        </SpotlightCard>
      ))}
    </div>
  );
}
