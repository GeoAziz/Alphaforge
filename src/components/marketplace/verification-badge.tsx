'use client';

import { ShieldCheck, ShieldAlert, Award, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";

interface VerificationBadgeProps {
  stage: number; // 1-5
  className?: string;
}

/**
 * VerificationBadge - Displays the 5-stage institutional audit status for marketplace strategies.
 */
export function VerificationBadge({ stage, className }: VerificationBadgeProps) {
  const getStageColor = (s: number) => {
    if (s >= 5) return 'text-green border-green/30 bg-green/10';
    if (s >= 3) return 'text-primary border-primary/30 bg-primary/10';
    return 'text-amber border-amber/30 bg-amber/10';
  };

  const getStageIcon = (s: number) => {
    if (s >= 5) return <Award size={12} />;
    if (s >= 3) return <ShieldCheck size={12} />;
    return <Shield size={12} />;
  };

  const getStageLabel = (s: number) => {
    switch(s) {
      case 5: return "Tier 5 Audit";
      case 4: return "Institutional Verified";
      case 3: return "Verified Node";
      case 2: return "Audit Pending";
      default: return "Self-Declared";
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn("flex flex-col gap-1.5 cursor-help", className)}>
            <div className={cn(
              "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[9px] font-black uppercase tracking-widest w-fit",
              getStageColor(stage)
            )}>
              {getStageIcon(stage)}
              {getStageLabel(stage)}
            </div>
            <div className="flex gap-1 w-full max-w-[100px]">
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
        <TooltipContent className="glass border-border-subtle p-3 max-w-[220px]">
          <div className="space-y-2">
            <div className="text-[10px] font-black uppercase text-primary">Audit Pipeline</div>
            <p className="text-[9px] font-bold uppercase leading-relaxed text-text-secondary">
              Stage {stage}/5 reached. This strategy has passed identity, logic, and 4-week paper-trade verification gates.
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
