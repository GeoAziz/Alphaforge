'use client';

import { Microscope, CheckCircle2, Clock, ShieldCheck, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * StepPaperTradeGate - Educational screen for mandatory 4-week validation.
 */
export function StepPaperTradeGate() {
  const timeline = [
    { label: "Phase 1: Initial Calibration", duration: "Week 1", status: "complete" },
    { label: "Phase 2: Live Logic Verification", duration: "Week 2-3", status: "active" },
    { label: "Phase 3: Execution Parity Check", duration: "Week 4", status: "pending" },
  ];

  return (
    <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500">
      <div className="space-y-4 text-center">
        <div className="w-16 h-16 rounded-3xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 mx-auto mb-6 shadow-inner">
          <Microscope size={32} className="animate-pulse" />
        </div>
        <h2 className="text-3xl font-black uppercase tracking-tighter leading-none">The Validation Gate</h2>
        <p className="text-sm text-text-muted font-medium uppercase tracking-tight max-w-sm mx-auto">
          Every signal node must pass a mandatory 4-week paper trading period before live execution is unlocked.
        </p>
      </div>

      <div className="p-6 rounded-2xl bg-elevated/20 border border-border-subtle space-y-6 relative overflow-hidden">
        <div className="relative z-10 space-y-6">
          {timeline.map((step, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center border shrink-0",
                step.status === 'complete' ? "bg-green/10 border-green/20 text-green" : 
                step.status === 'active' ? "bg-primary/10 border-primary/20 text-primary animate-pulse" : 
                "bg-elevated border-border-subtle text-text-muted"
              )}>
                {step.status === 'complete' ? <ShieldCheck size={16} /> : step.status === 'active' ? <Clock size={16} /> : <Zap size={16} />}
              </div>
              <div className="flex-1">
                <div className={cn(
                  "text-[11px] font-black uppercase tracking-tight",
                  step.status === 'pending' ? "text-text-muted" : "text-text-primary"
                )}>{step.label}</div>
                <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest">{step.duration} Timeline</div>
              </div>
            </div>
          ))}
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      </div>

      <div className="p-4 rounded-xl bg-primary/5 border border-primary/10">
        <p className="text-[10px] font-bold text-text-secondary uppercase text-center leading-relaxed">
          This gate ensures all algorithmic resolutions achieve ≥80% of their historical backtest Sharpe before connecting to real liquidity.
        </p>
      </div>
    </div>
  );
}
