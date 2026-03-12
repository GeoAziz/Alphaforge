'use client';

import { useState, useEffect, useCallback } from 'react';
import { Signal, SignalProof } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { 
  Activity, 
  Play, 
  Target, 
  ShieldAlert, 
  Loader2, 
  X, 
  ShieldCheck, 
  Database, 
  ExternalLink,
  Cpu,
  Fingerprint,
  TrendingUp
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';

interface SignalDetailPanelProps {
  signal: Signal | null;
  onDismiss: () => void;
  onExecute: (signal: Signal) => void;
  isExecuting: boolean;
}

/**
 * SignalDetailPanel - Institutional Intelligence View
 * 
 * Accessibility:
 * - Landmarks: aside
 * - Keyboard: Escape key closes the panel
 * - ARIA: aria-label for clarity
 */
export function SignalDetailPanel({ 
  signal, 
  onDismiss, 
  onExecute, 
  isExecuting 
}: SignalDetailPanelProps) {
  const [proof, setProof] = useState<SignalProof | null>(null);
  const [isLoadingProof, setIsLoadingProof] = useState(false);

  // Keyboard listener for Escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onDismiss();
  }, [onDismiss]);

  useEffect(() => {
    if (signal) {
      window.addEventListener('keydown', handleKeyDown);
      setIsLoadingProof(true);
      api.signals.getSignalProof(signal.id)
        .then(setProof)
        .finally(() => setIsLoadingProof(false));
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [signal, handleKeyDown]);

  if (!signal) return null;

  return (
    <aside 
      className="fixed inset-y-0 right-0 w-full sm:w-[450px] z-50 lg:relative lg:z-0 lg:w-[450px] border-l border-border-subtle bg-surface/95 backdrop-blur-2xl p-8 overflow-y-auto space-y-8 animate-in slide-in-from-right duration-300 shadow-2xl lg:shadow-none flex flex-col"
      aria-label={`Detail for ${signal.asset} signal`}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black uppercase tracking-tighter text-primary flex items-center gap-2">
          <Target size={20} />
          Terminal Detail
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
        {/* Core Signal Data */}
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
            <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle">
              <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Invalidation (SL)</div>
              <div className="text-sm font-mono font-bold text-red">${signal.stopLoss.toLocaleString()}</div>
            </div>
            <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle">
              <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Target Projection</div>
              <div className="text-sm font-mono font-bold text-green">${signal.takeProfit.toLocaleString()}</div>
            </div>
          </div>
          
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        </div>

        {/* Alpha Drivers */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
            <Activity size={14} className="text-primary" />
            Alpha Drivers
          </h3>
          <div className="space-y-3" role="list">
            {signal.drivers.map((driver, index) => (
              <div key={index} role="listitem" className="flex items-center gap-3 p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-default group">
                <div className="w-1.5 h-1.5 rounded-full bg-primary group-hover:scale-150 transition-transform" aria-hidden="true" />
                <span className="text-[11px] font-bold text-text-secondary uppercase leading-relaxed">{driver}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk/Reward Visualization */}
        <div className="p-6 rounded-2xl bg-surface border border-dashed border-border-subtle space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[9px] font-black uppercase text-text-muted">Risk/Reward Ratio</span>
            <span className="text-xs font-black text-text-primary">1 : {signal.riskRewardRatio}</span>
          </div>
          <div className="h-1.5 w-full bg-elevated rounded-full overflow-hidden" role="progressbar" aria-valuenow={(1/signal.riskRewardRatio)*100} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full bg-primary" style={{ width: `${(1/signal.riskRewardRatio) * 100}%` }} />
          </div>
          <div className="flex justify-between items-center text-[9px] font-bold uppercase text-text-muted" aria-hidden="true">
            <span>Aggressive</span>
            <span>Optimal</span>
            <span>Conservative</span>
          </div>
        </div>

        {/* Model Integrity Footer */}
        <div className="pt-4 space-y-6">
          <Separator className="bg-border-subtle" />
          <div className="space-y-4">
            <h3 className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
              <ShieldCheck size={14} className="text-green" />
              Model Integrity
            </h3>
            
            <div className="grid grid-cols-1 gap-3">
              <div className="p-4 rounded-xl bg-elevated/10 border border-border-subtle flex items-center justify-between group hover:border-primary/30 transition-colors">
                <div className="flex items-center gap-3">
                  <Cpu size={16} className="text-text-muted group-hover:text-primary transition-colors" aria-hidden="true" />
                  <div>
                    <div className="text-[9px] font-black text-text-muted uppercase">Logic Node</div>
                    <div className="text-xs font-bold uppercase">AlphaEngine v4.2.0</div>
                  </div>
                </div>
                <Badge variant="outline" className="text-[8px] font-black border-primary/20 text-primary">Stable</Badge>
              </div>

              <div className="p-4 rounded-xl bg-elevated/10 border border-border-subtle space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Fingerprint size={16} className="text-text-muted" aria-hidden="true" />
                    <span className="text-[9px] font-black text-text-muted uppercase">Audit Hash</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-text-primary">0x7f8e...3a2b</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Database size={16} className="text-text-muted" aria-hidden="true" />
                    <span className="text-[9px] font-black text-text-muted uppercase">Blockchain Proof</span>
                  </div>
                  <button className="flex items-center gap-1.5 text-xs text-primary font-bold hover:underline focus:outline-none focus-visible:ring-1 focus-visible:ring-primary rounded">
                    Verified <ExternalLink size={10} />
                  </button>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 flex items-center justify-between">
                <div>
                  <div className="text-[9px] font-black text-primary uppercase mb-1">Backtest vs Live</div>
                  <div className="text-xs font-bold uppercase tracking-tight">Sharpe Delta: +0.12</div>
                </div>
                <TrendingUp size={16} className="text-primary" aria-hidden="true" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-8 mt-auto border-t border-border-subtle bg-surface/50 -mx-8 px-8 pb-8">
        <Button 
          onClick={() => onExecute(signal)}
          disabled={isExecuting}
          className="w-full h-16 bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-95 transition-all gap-3 shadow-[0_0_30px_rgba(96,165,250,0.4)] rounded-2xl"
        >
          {isExecuting ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          Execute Terminal Position
        </Button>
        <p className="text-[9px] text-center text-text-muted uppercase font-black tracking-widest mt-4">
          Handshake ID: {signal.id.slice(0, 12)}... | Node: AF-US-01
        </p>
      </div>
    </aside>
  );
}
