'use client';

import { cn } from "@/lib/utils";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";
import { Copy, CheckCircle2, TrendingUp, Clock } from "lucide-react";
import { useState } from "react";

interface ConfidencePillProps {
  score: number;
  modelVersion?: string;
  auditHash?: string;
  livePerformance?: number; // 0-100% of backtest
}

/**
 * ConfidencePill - Enhanced institutional version with model telemetry tooltips.
 * Features hover expansion and clipboard integration for audit hashes.
 */
export function ConfidencePill({ 
  score, 
  modelVersion = "AlphaEngine v4.2.0", 
  auditHash = "0x7f8e...3a2b",
  livePerformance = 93.4
}: ConfidencePillProps) {
  const [copied, setCopied] = useState(false);

  let colorClass = "bg-red/10 text-red border-red/20";
  let dotClass = "bg-red";

  if (score >= 80) {
    colorClass = "bg-green/10 text-green border-green/20 shadow-[0_0_12px_rgba(52,211,153,0.15)]";
    dotClass = "bg-green";
  } else if (score >= 60) {
    colorClass = "bg-amber/10 text-amber border-amber/20";
    dotClass = "bg-amber";
  }

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(auditHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn(
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-black tracking-widest uppercase cursor-help transition-all hover:scale-105 active:scale-95 group",
            colorClass
          )}>
            <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", dotClass)} />
            {score}% CONFIDENCE
            <button 
              onClick={handleCopy}
              className="ml-1 hover:text-text-primary transition-colors opacity-40 group-hover:opacity-100"
              aria-label="Copy audit hash"
            >
              {copied ? <CheckCircle2 size={10} className="text-green" /> : <Copy size={10} />}
            </button>
          </div>
        </TooltipTrigger>
        <TooltipContent className="glass border-border-subtle p-4 w-64 space-y-3 shadow-2xl">
          <div className="space-y-1">
            <div className="text-[10px] font-black uppercase text-primary tracking-widest">Node Intelligence</div>
            <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase">
              <span>Logic Core</span>
              <span className="text-text-primary">{modelVersion}</span>
            </div>
          </div>
          
          <div className="space-y-1 border-t border-border-subtle pt-2">
            <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase">
              <span className="flex items-center gap-1"><Clock size={10} /> Gate Duration</span>
              <span className="text-text-primary">28 Days</span>
            </div>
            <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase">
              <span className="flex items-center gap-1"><TrendingUp size={10} /> Live Performance</span>
              <span className={cn(
                "font-black",
                livePerformance >= 80 ? "text-green" : "text-amber"
              )}>{livePerformance}% WR</span>
            </div>
          </div>

          <div className="pt-2 border-t border-border-subtle">
            <div className="text-[8px] font-black text-text-muted uppercase mb-1">Audit Anchor</div>
            <div className="text-[9px] font-mono text-text-secondary truncate bg-elevated/50 p-1.5 rounded border border-border-subtle">{auditHash}</div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
