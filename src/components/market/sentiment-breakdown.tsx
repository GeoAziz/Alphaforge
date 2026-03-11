'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

const sentiments = [
  { asset: 'BTC', score: 72, label: 'Very Bullish', color: 'green' },
  { asset: 'ETH', score: 58, label: 'Neutral', color: 'amber' },
  { asset: 'SOL', score: 81, label: 'Very Bullish', color: 'green' },
  { asset: 'LINK', score: 45, label: 'Bearish', color: 'red' },
];

export function SentimentBreakdown() {
  return (
    <SpotlightCard className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
          <Brain size={16} className="text-accent" />
          Market Sentiment (NLP)
        </h3>
      </div>

      <div className="space-y-4">
        {sentiments.map((sentiment, idx) => (
          <div key={idx} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black text-text-primary">{sentiment.asset}</span>
              <span className={cn(
                "text-xs font-black font-mono",
                sentiment.color === 'green' ? "text-green" : sentiment.color === 'red' ? "text-red" : "text-amber"
              )}>
                {sentiment.score}%
              </span>
            </div>
            <div className="w-full h-2 rounded-full bg-elevated/50 overflow-hidden">
              <div 
                className={cn(
                  "h-full transition-all duration-500",
                  sentiment.color === 'green' ? "bg-green" : sentiment.color === 'red' ? "bg-red" : "bg-amber"
                )}
                style={{ width: `${sentiment.score}%` }}
              />
            </div>
            <div className="text-[9px] font-bold text-text-muted uppercase">{sentiment.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-border-subtle">
        <div className="text-[10px] font-bold text-text-muted uppercase mb-3">Aggregate Signal</div>
        <div className="p-3 rounded-lg bg-green/10 border border-green/20">
          <div className="text-sm font-black text-green">⬆ Overall Bullish Bias</div>
          <div className="text-[9px] text-green/80 mt-1">3 out of 4 assets showing positive sentiment</div>
        </div>
      </div>
    </SpotlightCard>
  );
}
