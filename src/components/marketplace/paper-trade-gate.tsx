'use client';

import { Microscope, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface PaperTradeGateProps {
  passed: boolean;
  delta?: number;
  duration?: number;
}

/**
 * PaperTradeGate - Visual result of the mandatory 4-week simulation gate.
 */
export function PaperTradeGate({ passed, delta = 0, duration = 30 }: PaperTradeGateProps) {
  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-elevated/20 border border-border-subtle">
      <div className="flex items-center gap-3">
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center border",
          passed ? "bg-green/10 text-green border-green/20" : "bg-amber/10 text-amber border-amber/20"
        )}>
          {passed ? <CheckCircle2 size={16} /> : <Microscope size={16} />}
        </div>
        <div>
          <div className="text-[10px] font-black uppercase tracking-tight text-text-primary">
            {passed ? "Gate Passed" : "Gate In Progress"}
          </div>
          <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">
            Institutional Verification Gate
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={cn(
          "text-[10px] font-black font-mono",
          delta >= 0 ? "text-green" : "text-red"
        )}>
          {delta >= 0 ? '+' : ''}{delta}% Delta
        </div>
        <div className="text-[8px] font-black text-text-muted uppercase">
          {duration} Day Lock
        </div>
      </div>
    </div>
  );
}
