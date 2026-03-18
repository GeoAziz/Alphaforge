'use client';

import { useEffect } from 'react';
import { Signal } from '@/lib/types';
import { cn } from '@/lib/utils';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { GradientBorder } from '@/components/shared/gradient-border';
import { ConfidencePill } from '@/components/shared/confidence-pill';
import { useAnalytics } from '@/providers/posthog-provider';
import { Clock, TrendingUp } from 'lucide-react';

interface SignalCardProps {
  signal: Signal;
  onClick: (signal: Signal) => void;
  isSelected?: boolean;
  className?: string;
}

/**
 * SignalCard - High-density institutional signal preview.
 * Features conditional GradientBorder for high-confidence nodes (>= 85%).
 */
export function SignalCard({ signal, onClick, isSelected, className }: SignalCardProps) {
  const analytics = useAnalytics();
  const age = Date.now() - new Date(signal.createdAt).getTime();
  const isStale = age > 3600000; // 1hr+

  const handleClick = () => {
    // Track signal interaction
    analytics.signalInteraction('viewed', signal.id, signal.strategy);
    onClick(signal);
  };

  useEffect(() => {
    // Track signal appeared in view
    analytics.action('signal_appeared', {
      signal_id: signal.id,
      asset: signal.asset,
      direction: signal.direction,
      confidence: signal.confidence,
    });
  }, [signal.id, analytics, signal]);

  return (
    <div className={cn("transition-all duration-300", isStale && "opacity-60 grayscale-[0.5]", className)}>
      <GradientBorder active={signal.confidence >= 85}>
        <SpotlightCard 
          onClick={handleClick}
          className={cn(
            "p-6 cursor-pointer group bg-transparent border-none",
            isSelected && "bg-primary/5"
          )}
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className={cn(
                "px-3 py-1 rounded text-[10px] font-black uppercase tracking-widest h-max",
                signal.direction === 'LONG' ? "bg-green/10 text-green border border-green/20" : "bg-red/10 text-red border border-red/20"
              )}>
                {signal.direction}
              </div>
              <div>
                <div className="text-xl font-black tracking-tighter uppercase group-hover:text-primary transition-colors">
                  {signal.asset}
                </div>
                <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest flex items-center gap-2 mt-0.5">
                  {signal.strategy}
                  <div className="w-1 h-1 rounded-full bg-border-subtle" />
                  <span className="flex items-center gap-1"><Clock size={10} /> {new Date(signal.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 lg:gap-12">
              <div>
                <div className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-1">Threshold</div>
                <div className="text-xs font-mono font-bold">${signal.entryPrice.toLocaleString()}</div>
              </div>
              <div className="hidden sm:block">
                <div className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-1">R:R Node</div>
                <div className="text-xs font-mono font-bold">1:{signal.riskRewardRatio}</div>
              </div>
              <div className="flex items-center justify-end md:col-span-2 gap-4">
                {signal.pnlPercent !== null && (
                  <div className={cn(
                    "text-xs font-black font-mono flex items-center gap-1",
                    signal.pnlPercent >= 0 ? "text-green" : "text-red"
                  )}>
                    <TrendingUp size={12} className={cn(signal.pnlPercent < 0 && "rotate-180")} />
                    {signal.pnlPercent > 0 ? '+' : ''}{signal.pnlPercent}%
                  </div>
                )}
                <ConfidencePill score={signal.confidence} />
              </div>
            </div>
          </div>
        </SpotlightCard>
      </GradientBorder>
    </div>
  );
}
