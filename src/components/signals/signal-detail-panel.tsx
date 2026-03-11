'use client';

import { Signal } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Play, Target, ShieldAlert, Loader2, X } from 'lucide-react';

interface SignalDetailPanelProps {
  signal: Signal | null;
  onDismiss: () => void;
  onExecute: (signal: Signal) => void;
  isExecuting: boolean;
}

/**
 * SignalDetailPanel provides the third-panel contextual view for deep signal analysis.
 * Features institutional risk/reward metrics and alpha driver rationale.
 */
export function SignalDetailPanel({ 
  signal, 
  onDismiss, 
  onExecute, 
  isExecuting 
}: SignalDetailPanelProps) {
  if (!signal) return null;

  return (
    <aside className="fixed inset-y-0 right-0 w-full sm:w-[450px] z-50 lg:relative lg:z-0 lg:w-[450px] border-l border-border-subtle bg-surface/90 backdrop-blur-xl p-8 overflow-y-auto space-y-8 animate-in slide-in-from-right duration-300 shadow-2xl lg:shadow-none">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black uppercase tracking-tighter text-primary flex items-center gap-2">
          <Target size={20} />
          Terminal Detail
        </h2>
        <button 
          onClick={onDismiss}
          className="p-2 text-text-muted hover:text-text-primary transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      <div className="space-y-6">
        <div className="p-6 rounded-2xl bg-elevated/50 border border-border-subtle shadow-inner relative overflow-hidden group">
          <div className="flex items-center justify-between mb-6 relative z-10">
            <div>
              <div className="text-3xl font-black tracking-tighter group-hover:scale-105 transition-transform duration-500">{signal.asset}</div>
              <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mt-1">Institutional Consensus</div>
            </div>
            <Badge className={cn(
              "font-black uppercase tracking-widest h-8 px-4",
              signal.direction === 'LONG' ? "bg-green/10 text-green border-green/20" : "bg-red/10 text-red border-red/20"
            )}>
              {signal.direction}
            </Badge>
          </div>
          
          <div className="grid grid-cols-2 gap-4 relative z-10">
            <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle hover:border-red/30 transition-colors">
              <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Invalidation (SL)</div>
              <div className="text-sm font-mono font-bold text-red">${signal.stopLoss.toLocaleString()}</div>
            </div>
            <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle hover:border-green/30 transition-colors">
              <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Target Projection</div>
              <div className="text-sm font-mono font-bold text-green">${signal.takeProfit.toLocaleString()}</div>
            </div>
          </div>
          
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        </div>

        <div className="space-y-4">
          <h3 className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
            <Activity size={14} className="text-primary" />
            Alpha Drivers
          </h3>
          <div className="space-y-3">
            {signal.drivers.map((driver, index) => (
              <div key={index} className="flex items-center gap-3 p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-default group">
                <div className="w-1.5 h-1.5 rounded-full bg-primary group-hover:scale-150 transition-transform" />
                <span className="text-[11px] font-bold text-text-secondary uppercase leading-relaxed">{driver}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-surface border border-dashed border-border-subtle">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[9px] font-black uppercase text-text-muted">Risk/Reward Ratio</span>
            <span className="text-xs font-black text-text-primary">1 : {signal.riskRewardRatio}</span>
          </div>
          <div className="h-1.5 w-full bg-elevated rounded-full overflow-hidden">
            <div className="h-full bg-primary" style={{ width: `${(1/signal.riskRewardRatio) * 100}%` }} />
          </div>
        </div>
      </div>

      <div className="pt-8 mt-auto">
        <Button 
          onClick={() => onExecute(signal)}
          disabled={isExecuting}
          className="w-full h-16 bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-95 transition-all gap-3 shadow-[0_0_30px_rgba(96,165,250,0.4)] rounded-2xl"
        >
          {isExecuting ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          Execute Terminal Position
        </Button>
        <p className="text-[9px] text-center text-text-muted uppercase font-black tracking-widest mt-4">
          Margin utilization pre-calculated for {signal.asset} cluster.
        </p>
      </div>
    </aside>
  );
}
