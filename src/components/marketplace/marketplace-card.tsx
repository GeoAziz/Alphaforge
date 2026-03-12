'use client';

import { MarketplaceStrategy } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { VerificationBadge } from './verification-badge';
import { ReputationScore } from '@/components/shared/reputation-score';
import { PaperTradeGate } from './paper-trade-gate';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Zap, ShoppingBag, Loader2, ArrowRight } from 'lucide-react';

interface MarketplaceCardProps {
  strategy: MarketplaceStrategy;
  onSubscribe: (strategy: MarketplaceStrategy) => void;
  isSubscribing: boolean;
}

/**
 * MarketplaceCard - Institutional strategy node listing.
 * Features 5-stage verification, paper-trade gate, and reputation telemetry.
 */
export function MarketplaceCard({ strategy, onSubscribe, isSubscribing }: MarketplaceCardProps) {
  return (
    <SpotlightCard variant="accent" className="p-0 flex flex-col border-primary/5 hover:border-primary/20 transition-all group overflow-hidden">
      <div className="p-6 lg:p-8 flex-1 space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-2xl bg-elevated flex items-center justify-center text-xl font-black border border-border-subtle shadow-inner">
              {strategy.name[0]}
            </div>
            <div>
              <h3 className="text-xl font-black tracking-tighter group-hover:text-primary transition-colors leading-none uppercase">
                {strategy.name}
              </h3>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-widest">{strategy.creator}</span>
                <ReputationScore score={strategy.reputationScore} />
              </div>
            </div>
          </div>
          <Badge variant="outline" className={cn(
            "text-[9px] font-black uppercase border-primary/20",
            strategy.riskLevel === 'High' ? "text-red border-red/20" : "text-primary"
          )}>
            {strategy.riskLevel} Risk
          </Badge>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed font-medium line-clamp-3 uppercase">
          {strategy.description}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { l: 'Efficiency', v: `${strategy.winRate}%`, c: 'text-green' },
            { l: 'Drawdown', v: `${strategy.maxDrawdown}%`, c: 'text-red' },
            { l: 'Nodes', v: strategy.subscribers.toLocaleString(), c: 'text-text-primary' },
            { l: 'Sharpe', v: strategy.sharpeRatio.toFixed(2), c: 'text-primary' }
          ].map(m => (
            <div key={m.l} className="p-2.5 rounded-xl bg-surface border border-border-subtle space-y-1">
              <div className="text-[8px] font-black text-text-muted uppercase">{m.l}</div>
              <div className={cn("text-xs font-black font-mono", m.c)}>{m.v}</div>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <VerificationBadge stage={strategy.verificationStage} />
          <PaperTradeGate passed={strategy.isVerified} delta={strategy.paperTradeDelta} />
        </div>

        <div className="pt-4 border-t border-border-subtle/50 flex items-center justify-between">
          <div className="text-left">
            <div className="text-[9px] font-black uppercase text-text-muted mb-1">ROI Trailing 12M</div>
            <div className="text-3xl font-black text-green font-mono tracking-tighter">+{strategy.roi}%</div>
          </div>
          {strategy.performanceBadge && (
            <Badge className="bg-primary/20 text-primary border-primary/30 uppercase font-black text-[8px] tracking-widest px-3 h-6">
              {strategy.performanceBadge}
            </Badge>
          )}
        </div>
      </div>

      <div className="bg-elevated/30 border-t border-border-subtle p-6 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-6 w-full sm:w-auto">
          <div className="space-y-1">
            <div className="text-[9px] font-black uppercase text-text-muted">Node Fee</div>
            <div className="text-xl font-black font-mono">${strategy.monthlyPrice}<span className="text-[10px] text-text-muted">/mo</span></div>
          </div>
          <div className="h-8 w-px bg-border-subtle" />
          <Badge variant="outline" className="text-[8px] font-black uppercase border-primary/20 text-primary">{strategy.pricingModel}</Badge>
        </div>
        
        <Button 
          onClick={() => onSubscribe(strategy)}
          disabled={isSubscribing}
          className="w-full sm:w-[180px] bg-primary text-primary-foreground font-black uppercase text-[10px] h-12 gap-2 rounded-xl group-hover:scale-[1.02] transition-transform"
        >
          {isSubscribing ? <Loader2 className="animate-spin" size={16} /> : <ShoppingBag size={16} />}
          Establish Sync
        </Button>
      </div>
    </SpotlightCard>
  );
}
