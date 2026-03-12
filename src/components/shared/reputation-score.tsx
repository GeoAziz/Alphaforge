'use client';

import { Star, ShieldCheck, Users, TrendingUp, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";

interface ReputationScoreProps {
  score: number;
  className?: string;
}

/**
 * ReputationScore - Displays creator metrics with institutional polish and detail popover.
 */
export function ReputationScore({ score, className }: ReputationScoreProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <div className={cn("flex items-center gap-1.5 cursor-help group", className)}>
          <div className="flex -space-x-0.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star 
                key={i} 
                size={10} 
                className={cn(
                  "transition-all duration-300",
                  i <= Math.floor(score) ? "text-amber fill-current" : "text-text-muted opacity-30",
                  "group-hover:scale-110"
                )} 
              />
            ))}
          </div>
          <span className="text-[10px] font-black text-amber uppercase tracking-widest">{score.toFixed(1)} Rep</span>
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-64 glass border-border-subtle p-4 shadow-2xl">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-[10px] font-black uppercase text-primary tracking-widest">Creator Rep Node</h4>
            <div className="text-amber font-black text-xs">{score}/5.0</div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[9px] font-bold uppercase text-text-muted">
              <div className="flex items-center gap-2"><ShieldCheck size={12} className="text-green" /> Verification</div>
              <div className="text-text-primary">Passed</div>
            </div>
            <div className="flex items-center justify-between text-[9px] font-bold uppercase text-text-muted">
              <div className="flex items-center gap-2"><Users size={12} className="text-primary" /> Active Nodes</div>
              <div className="text-text-primary">1,240</div>
            </div>
            <div className="flex items-center justify-between text-[9px] font-bold uppercase text-text-muted">
              <div className="flex items-center gap-2"><TrendingUp size={12} className="text-accent" /> Alpha Stability</div>
              <div className="text-text-primary">High</div>
            </div>
          </div>

          <div className="p-2 rounded bg-elevated/20 border border-border-subtle text-[8px] text-text-muted italic leading-relaxed uppercase">
            Reputation is derived from node stability, draw-down recovery factors, and verified user feedback loops.
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
