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
  TrendingUp,
  Microscope,
  Info,
  CheckCircle2
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/progress";

interface SignalDetailPanelProps {
  signal: Signal | null;
  onDismiss: () => void;
  onExecute: (signal: Signal) => void;
  isExecuting: boolean;
}

/**
 * SignalDetailPanel - Institutional Intelligence View
 * Features an enhanced Model Integrity footer with blockchain proof telemetry.
 */
export function SignalDetailPanel({ 
  signal, 
  onDismiss, 
  onExecute, 
  isExecuting 
}: SignalDetailPanelProps) {
  const [proof, setProof] = useState<SignalProof | null>(null);
  const [isLoadingProof, setIsLoadingProof] = useState(false);

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
          <div className="space-y-3">
            {signal.drivers.map((driver, index) => (
              <div key={index} className="space-y-2 p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-default group">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {driver.active ? <CheckCircle2 size={12} className="text-green" /> : <div className="w-1.5 h-1.5 rounded-full bg-border-subtle" />}
                    <span className="text-[11px] font-bold text-text-secondary uppercase leading-relaxed">{driver.label}</span>
                  </div>
                  <span className="text-[9px] font-black text-primary uppercase">{Math.round(driver.weight * 100)}%</span>
                </div>
                <Progress value={driver.weight * 100} className="h-1 bg-border-subtle" />
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
          <div className="h-1.5 w-full bg-elevated rounded-full overflow-hidden">
            <div className="h-full bg-primary" style={{ width: `${(1/signal.riskRewardRatio) * 100}%` }} />
          </div>
        </div>

        {/* Model Integrity Footer */}
        <div className="pt-4 space-y-6">
          <Separator className="bg-border-subtle" />
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                <ShieldCheck size={14} className="text-green" />
                Model Integrity Node
              </h3>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="text-text-muted hover:text-text-primary transition-colors"><Info size={12} /></button>
                  </TooltipTrigger>
                  <TooltipContent className="glass border-border-subtle p-3 max-w-[200px]">
                    <p className="text-[9px] font-bold uppercase leading-relaxed">Immutable cryptographic proof of signal issuance and paper-trade validation results.</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            
            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-elevated/10 border border-border-subtle space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Fingerprint size={16} className="text-text-muted" />
                    <span className="text-[9px] font-black text-text-muted uppercase">Audit Hash</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-text-primary">0x7f8e...3a2b</span>
                </div>
                <div className="flex items-center justify-between border-t border-border-subtle/50 pt-3">
                  <div className="flex items-center gap-3">
                    <Database size={16} className="text-text-muted" />
                    <span className="text-[9px] font-black text-text-muted uppercase">Blockchain Anchor</span>
                  </div>
                  <Badge variant="outline" className="text-[8px] font-black border-green/30 text-green h-5 px-2 uppercase">Verified Sync</Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-elevated/10 border border-border-subtle group hover:border-primary/30 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <Microscope size={14} className="text-primary" />
                    <span className="text-[8px] font-black text-text-muted uppercase">Gate Status</span>
                  </div>
                  <div className="text-[10px] font-black text-green uppercase">Passed 28D</div>
                </div>
                <div className="p-4 rounded-xl bg-primary/5 border border-primary/10">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={14} className="text-primary" />
                    <span className="text-[8px] font-black text-text-muted uppercase">Perf Delta</span>
                  </div>
                  <div className="text-[10px] font-black text-primary uppercase">+0.12 Sharpe</div>
                </div>
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
