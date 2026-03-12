'use client';

import { CheckCircle2, ShieldCheck, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";

interface VerificationBadgeProps {
  stage?: number;
  className?: string;
}

/**
 * VerificationBadge - Shows 5-stage institutional verification status with color coding.
 */
export function VerificationBadge({ stage = 5, className }: VerificationBadgeProps) {
  // Determine color based on stage
  const getStageColor = (s: number) => {
    if (s >= 5) return 'text-green border-green/30 bg-green/10';
    if (s >= 3) return 'text-primary border-primary/30 bg-primary/10';
    return 'text-amber border-amber/30 bg-amber/10';
  };

  const getStageDescription = (s: number) => {
    switch(s) {
      case 5: return "Full institutional audit: Performance, Code, and Latency verified.";
      case 4: return "Advanced verification: High-frequency performance verified.";
      case 3: return "Basic audit: Backtest results and basic code stability confirmed.";
      case 2: return "Initial screening complete. Peer review pending.";
      default: return "Self-declared performance. Proceed with extreme caution.";
    }
  };

  const colorClasses = getStageColor(stage);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn("flex flex-col gap-1.5 cursor-help", className)}>
            <div className={cn(
              "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[9px] font-black uppercase tracking-widest w-fit",
              colorClasses
            )}>
              {stage >= 3 ? <ShieldCheck size={10} /> : <AlertCircle size={10} />}
              {stage}-Stage Verified
            </div>
            <div className="flex gap-1 w-full">
              {Array.from({ length: 5 }).map((_, i) => (
                <div 
                  key={i} 
                  className={cn(
                    "h-1 flex-1 rounded-full transition-all duration-500",
                    i < stage 
                      ? (stage >= 5 ? "bg-green" : stage >= 3 ? "bg-primary" : "bg-amber") 
                      : "bg-elevated"
                  )} 
                />
              ))}
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent className="glass border-border-subtle p-3 max-w-[200px]">
          <p className="text-[10px] font-bold uppercase leading-relaxed text-text-primary">
            {getStageDescription(stage)}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
