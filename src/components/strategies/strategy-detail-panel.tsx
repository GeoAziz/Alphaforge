'use client';

import { Strategy, PaperTradeResult } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { 
  X, 
  TrendingUp, 
  Target, 
  BarChart3, 
  Loader2,
  Info,
  Zap,
  ShieldCheck,
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { useCallback, useEffect, useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface StrategyDetailPanelProps {
  strategy: Strategy | null;
  onDismiss: () => void;
  onSubscribe?: (strategy: Strategy) => void;
}

/**
 * StrategyDetailPanel - Full strategy performance breakdown.
 * Shows detailed metrics, historical performance, and subscription options.
 */
export function StrategyDetailPanel({ strategy, onDismiss, onSubscribe }: StrategyDetailPanelProps) {
  const [paperTradeResult, setPaperTradeResult] = useState<PaperTradeResult | null>(null);
  const [isLoadingPaperTrade, setIsLoadingPaperTrade] = useState(false);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onDismiss();
  }, [onDismiss]);

  useEffect(() => {
    if (strategy) {
      window.addEventListener('keydown', handleKeyDown);
      // Fetch paper trade result if available
      if (strategy.id) {
        setIsLoadingPaperTrade(true);
        api.strategies.getStrategyPaperTradeResult(strategy.id).then(setPaperTradeResult).finally(() => setIsLoadingPaperTrade(false));
      }
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [strategy, handleKeyDown]);

  if (!strategy) return null;

  return (
    <aside 
      className="fixed inset-y-0 right-0 w-full sm:w-[480px] z-50 lg:relative lg:z-0 lg:w-[480px] border-l border-border-subtle bg-surface/95 backdrop-blur-2xl p-8 overflow-y-auto space-y-8 animate-in slide-in-from-right duration-300 shadow-2xl lg:shadow-none flex flex-col"
      aria-label={`Details for ${strategy.name} strategy`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black uppercase tracking-tighter text-primary flex items-center gap-2">
          <Target size={20} />
          Strategy Details
        </h2>
        <button 
          onClick={onDismiss}
          className="p-2 text-text-muted hover:text-text-primary transition-colors focus-visible:ring-2 focus-visible:ring-primary rounded-lg outline-none"
          aria-label="Dismiss detail panel"
        >
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 space-y-8">
        {/* Title & Description */}
        <div>
          <h3 className="text-3xl font-black tracking-tighter leading-none mb-2">{strategy.name}</h3>
          <p className="text-sm text-text-secondary font-medium">{strategy.description}</p>
        </div>

        {/* Core Metrics */}
        <div className="grid grid-cols-2 gap-4 p-6 rounded-2xl bg-elevated/50 border border-border-subtle">
          <div>
            <div className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">Win Rate</div>
            <div className="text-2xl font-black text-green">{strategy.winRate.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">Avg ROI</div>
            <div className="text-2xl font-black text-primary">+{strategy.avgRoi.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">Sharpe</div>
            <div className="text-2xl font-black text-text-primary">{strategy.sharpeRatio?.toFixed(2) || '—'}</div>
          </div>
          <div>
            <div className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">Max DD</div>
            <div className="text-2xl font-black text-red">{strategy.maxDrawdown?.toFixed(1) || '—'}%</div>
          </div>
        </div>

        <Separator />

        {/* Risk Level */}
        <div className="space-y-3">
          <h3 className="text-xs font-black uppercase text-text-muted tracking-widest">Risk Profile</h3>
          <Badge 
            className={cn(
              'font-black uppercase text-[11px] h-8 px-4',
              strategy.riskLevel === 'High' ? 'bg-red/10 text-red border-red/20' :
              strategy.riskLevel === 'Medium' ? 'bg-amber/10 text-amber border-amber/20' :
              'bg-green/10 text-green border-green/20'
            )}
          >
            {strategy.riskLevel} Risk{strategy.maxLeverage ? ` — ${strategy.maxLeverage}x Max Leverage` : ''}
          </Badge>
        </div>

        {/* Paper Trading Result  */}
        {paperTradeResult && (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                  <ShieldCheck size={12} className="text-green" />
                  Paper Trading Results
                </h3>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="text-text-muted hover:text-text-primary">
                        <Info size={12} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="glass border-border-subtle p-2 max-w-[200px]">
                      <p className="text-[9px] font-bold uppercase leading-relaxed">
                        Results from {paperTradeResult.duration.toFixed(0)}-day paper trading validation
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-green/5 border border-green/20">
                <div>
                  <div className="text-[8px] font-black text-green uppercase tracking-widest mb-1">Duration</div>
                  <div className="font-black text-text-primary">{paperTradeResult.duration.toFixed(0)}d</div>
                </div>
                <div>
                  <div className="text-[8px] font-black text-green uppercase tracking-widest mb-1">Signals</div>
                  <div className="font-black text-text-primary">{paperTradeResult.signalCount}</div>
                </div>
                <div>
                  <div className="text-[8px] font-black text-green uppercase tracking-widest mb-1">ROI</div>
                  <div className="font-black text-green">+{paperTradeResult.roi.toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-[8px] font-black text-green uppercase tracking-widest mb-1">DD</div>
                  <div className="font-black text-text-primary">{paperTradeResult.maxDrawdown.toFixed(1)}%</div>
                </div>
              </div>
            </div>
          </>
        )}

        
        {/* Additional Attributes */}
        <Separator />
        <div className="space-y-3">
          <h3 className="text-xs font-black uppercase text-text-muted tracking-widest">Configuration</h3>
          <div className="space-y-2">
            {strategy.signals && (
              <div className="flex items-center justify-between p-2 rounded-lg bg-elevated/30">
                <span className="text-[9px] font-bold text-text-muted uppercase">Active Signals</span>
                <span className="text-[10px] font-black text-text-primary">{strategy.signals}</span>
              </div>
            )}
            {strategy.status && (
              <div className="flex items-center justify-between p-2 rounded-lg bg-elevated/30">
                <span className="text-[9px] font-bold text-text-muted uppercase">Status</span>
                <Badge variant="outline" className="text-[8px] font-black uppercase border-text-muted/20 text-text-muted px-2 h-5">
                  {strategy.status}
                </Badge>
              </div>
            )}
            {strategy.createdAt && (
              <div className="flex items-center justify-between p-2 rounded-lg bg-elevated/30">
                <span className="text-[9px] font-bold text-text-muted uppercase">Deployed</span>
                <span className="text-[10px] font-bold text-text-secondary font-mono">
                  {new Date(strategy.createdAt).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CTA Footer */}
      <div className="pt-8 mt-auto border-t border-border-subtle bg-surface/50 -mx-8 px-8 pb-8">
        <Button 
          onClick={() => onSubscribe?.(strategy)}
          disabled={isLoadingPaperTrade}
          className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-95 transition-all gap-3 shadow-[0_0_30px_rgba(96,165,250,0.4)] rounded-2xl"
        >
          {isLoadingPaperTrade ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
          Subscribe to Strategy
        </Button>
        <p className="text-[8px] text-center text-text-muted uppercase font-black tracking-widest mt-4">
          Node: {strategy.id?.slice(0, 12)}... | Active
        </p>
      </div>
    </aside>
  );
}
