'use client';

import { ExternalSignal } from '@/lib/types';
import { ExternalSignalCard } from './external-signal-card';
import { Zap } from 'lucide-react';

interface ExternalSignalFeedProps {
  signals: ExternalSignal[];
  isLoading?: boolean;
}

export function ExternalSignalFeed({ signals, isLoading }: ExternalSignalFeedProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array(3).fill(0).map((_, i) => (
          <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
        ))}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="py-20 text-center space-y-4 rounded-2xl border border-dashed border-border-subtle bg-surface/30">
        <div className="w-12 h-12 rounded-full bg-elevated mx-auto flex items-center justify-center text-text-muted opacity-30">
          <Zap size={24} />
        </div>
        <div className="space-y-1">
          <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">No External Telemetry Detected.</div>
          <p className="text-[9px] font-bold text-text-muted uppercase">Set up a TradingView webhook to begin ingestion.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {signals.map((signal) => (
        <ExternalSignalCard key={signal.id} signal={signal} />
      ))}
    </div>
  );
}
