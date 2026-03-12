'use client';

import { cn } from "@/lib/utils";
import { ShieldCheck, ShieldAlert, WifiOff, AlertCircle } from "lucide-react";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";

interface DataQualityIndicatorProps {
  status: 'Optimal' | 'Degraded' | 'Offline' | 'Stale' | 'Anomaly';
  latency?: number;
  className?: string;
  asset?: string;
}

/**
 * DataQualityIndicator - Visual status node for institutional data feeds.
 * Features pulse animations for anomalies and detailed diagnostic tooltips.
 */
export function DataQualityIndicator({ status, latency, className, asset }: DataQualityIndicatorProps) {
  const isAnomaly = status === 'Anomaly' || status === 'Stale';

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn(
            "inline-flex items-center gap-2 px-2.5 py-1 rounded-lg border text-[9px] font-black uppercase tracking-tighter cursor-help transition-all",
            status === 'Optimal' && "bg-green/10 text-green border-green/20",
            status === 'Degraded' && "bg-amber/10 text-amber border-amber/20",
            status === 'Offline' && "bg-red/10 text-red border-red/20",
            isAnomaly && "bg-red/5 text-red border-red/30 animate-pulse",
            className
          )}>
            <div className="relative flex items-center justify-center">
              {status === 'Optimal' && <ShieldCheck size={12} />}
              {(status === 'Degraded' || isAnomaly) && <ShieldAlert size={12} />}
              {status === 'Offline' && <WifiOff size={12} />}
              
              {isAnomaly && (
                <span className="absolute inset-0 rounded-full animate-anomaly" />
              )}
            </div>
            
            <span className="hidden xs:inline">Feed {status}</span>
            
            {latency && (
              <>
                <div className="w-px h-2.5 bg-current opacity-20 mx-1" />
                <span className="font-mono">{latency}ms</span>
              </>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent className="glass border-border-subtle p-3 max-w-[240px]">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase text-primary">Diagnostic Node</span>
              <span className="text-[9px] font-black text-text-muted">{asset} Handshake</span>
            </div>
            <p className="text-[9px] font-bold uppercase leading-relaxed text-text-secondary">
              {status === 'Optimal' && "Latency optimized via high-frequency Binance WebSocket cluster."}
              {status === 'Anomaly' && "Price moved 4.2σ from mean. Institutional logic quarantined."}
              {status === 'Stale' && "No telemetry received for >60s. Switching to Polygon.io backup."}
              {status === 'Degraded' && "Network jitter detected. Accuracy threshold reduced to 85%."}
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
