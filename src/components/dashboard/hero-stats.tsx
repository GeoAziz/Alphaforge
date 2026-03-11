"use client";

import { AnimatedCounter } from "@/components/shared/animated-counter";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { PortfolioSummary } from "@/lib/types";

interface HeroStatsProps {
  summary?: PortfolioSummary | null;
}

export function HeroStats({ summary }: HeroStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="md:col-span-2 relative overflow-hidden flex flex-col justify-center p-8 rounded-2xl border border-primary/20 bg-primary/5 noise-surface--subtle">
        <div className="text-xs font-bold uppercase tracking-widest text-primary/70 mb-2">Institutional Win Rate</div>
        <div className="text-hero gradient-text mb-4">
          <AnimatedCounter value={67.3} suffix="%" decimals={1} />
        </div>
        <div className="text-sm text-muted-foreground max-w-sm">
          System-wide performance aggregated across all active algorithmic strategies in the last 90 trading days.
        </div>
        {/* Decorative background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary/10 rounded-full blur-[100px] pointer-events-none" />
      </div>

      <div className="grid grid-cols-1 gap-6 md:col-span-2">
        <div className="grid grid-cols-2 gap-6">
          <SpotlightCard className="p-6">
            <div className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">Total Managed Trades</div>
            <div className="text-3xl font-bold">
              <AnimatedCounter value={summary?.totalTrades || 0} />
            </div>
            <div className="text-xs text-green mt-2 font-medium">Session History</div>
          </SpotlightCard>
          <SpotlightCard className="p-6" variant="accent">
            <div className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">Profit Factor</div>
            <div className="text-3xl font-bold">
              <AnimatedCounter value={1.94} decimals={2} />
            </div>
            <div className="text-xs text-primary mt-2 font-medium">Institutional Grade</div>
          </SpotlightCard>
        </div>
        <SpotlightCard className="p-6">
          <div className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">Global Unrealized ROI</div>
          <div className="flex items-baseline gap-2">
            <div className="text-4xl font-bold text-green">
              <AnimatedCounter value={(summary?.unrealizedPnl || 0) / (summary?.totalEquity || 1) * 100} prefix="+" suffix="%" decimals={2} />
            </div>
            <div className="text-xs text-text-muted">current exposure</div>
          </div>
          <div className="mt-4 h-1 w-full bg-border-subtle rounded-full overflow-hidden">
            <div className="h-full bg-green w-[65%]" />
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
