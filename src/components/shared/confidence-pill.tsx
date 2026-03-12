
'use client';

import { cn } from "@/lib/utils";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";
import { Copy, CheckCircle2 } from "lucide-react";
import { useState } from "react";

interface ConfidencePillProps {
  score: number;
  modelVersion?: string;
  auditHash?: string;
}

/**
 * ConfidencePill - Enhanced version with model version tooltips and clipboard copy.
 */
export function ConfidencePill({ 
  score, 
  modelVersion = "AlphaEngine v4.2", 
  auditHash = "0x7f8e...3a2b" 
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
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-black tracking-widest uppercase cursor-help transition-all hover:scale-105",
            colorClass
          )}>
            <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", dotClass)} />
            {score}% CONFIDENCE
            <button 
              onClick={handleCopy}
              className="ml-1 hover:text-text-primary transition-colors"
              title="Copy Audit Hash"
            >
              {copied ? <CheckCircle2 size={10} className="text-green" /> : <Copy size={10} />}
            </button>
          </div>
        </TooltipTrigger>
        <TooltipContent className="glass border-border-subtle p-3">
          <div className="space-y-1">
            <div className="text-[10px] font-black uppercase text-primary">Model Intelligence</div>
            <div className="text-[9px] font-bold text-text-muted uppercase">Logic: {modelVersion}</div>
            <div className="text-[9px] font-mono text-text-muted truncate w-32">Hash: {auditHash}</div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
