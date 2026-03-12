'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { PortfolioSummary } from '@/lib/types';
import { Skeleton } from '@/components/ui/skeleton';
import { ShieldCheck, Activity, TrendingUp, Zap } from 'lucide-react';

interface HeroSectionProps {
  summary?: PortfolioSummary | null;
  isLoading?: boolean;
}

export function HeroSection({ summary, isLoading }: HeroSectionProps) {
  return (
    <SpotlightCard variant="accent" className="h-full p-8 flex flex-col justify-between border-primary/20 bg-primary/5 relative overflow-hidden group">
      <div className="relative z-10 space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary border border-primary/30 shadow-[0_0_15px_rgba(96,165,250,0.3)]">
              <ShieldCheck size={18} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-primary/70">Institutional Win Rate</span>
          </div>
          <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-green/10 border border-green/20">
            <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
            <span className="text-[8px] font-black text-green uppercase tracking-tighter">Engine Active</span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-hero font-black tracking-tighter gradient-text leading-none transition-transform group-hover:scale-[1.02] duration-500">
            <AnimatedCounter value={68.4} suffix="%" decimals={1} />
          </div>
          <p className="text-sm text-text-secondary font-medium max-w-[300px] leading-relaxed">
            System-wide algorithmic performance aggregated across all authorized clusters in the last 90 trading days.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-xl bg-surface/40 border border-border-subtle group-hover:border-primary/30 transition-colors">
            <div className="text-[9px] font-black uppercase text-text-muted mb-1 flex items-center gap-1">
              <Zap size={10} className="text-primary" /> Profit Factor
            </div>
            <div className="text-lg font-black font-mono">2.15</div>
          </div>
          <div className="p-3 rounded-xl bg-surface/40 border border-border-subtle group-hover:border-accent/30 transition-colors">
            <div className="text-[9px] font-black uppercase text-text-muted mb-1 flex items-center gap-1">
              <TrendingUp size={10} className="text-accent" /> Avg. ROI
            </div>
            <div className="text-lg font-black font-mono">+12.4%</div>
          </div>
        </div>
      </div>

      <div className="relative z-10 pt-8 mt-8 border-t border-border-subtle">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Managed Equity</span>
          <Activity size={14} className="text-primary opacity-50" />
        </div>
        <div className="text-3xl font-black font-mono tracking-tighter text-text-primary">
          {isLoading ? <Skeleton className="h-9 w-32" /> : <AnimatedCounter value={summary?.totalEquity || 0} prefix="$" decimals={2} />}
        </div>
        <div className="mt-2 text-[10px] font-bold text-primary flex items-center gap-1 uppercase tracking-widest">
          Consensus Accuracy: 94.2%
        </div>
      </div>

      {/* Decorative background mesh gradient */}
      <div className="absolute -bottom-24 -right-24 w-80 h-80 bg-primary/10 rounded-full blur-[100px] pointer-events-none group-hover:bg-primary/15 transition-all duration-1000" />
      <div className="absolute -top-24 -left-24 w-64 h-64 bg-accent/5 rounded-full blur-[80px] pointer-events-none group-hover:bg-accent/10 transition-all duration-1000" />
    </SpotlightCard>
  );
}