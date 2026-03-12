
'use client';

import { cn } from "@/lib/utils";
import { ShieldCheck, ShieldAlert, WifiOff } from "lucide-react";

interface DataQualityIndicatorProps {
  status: 'Optimal' | 'Degraded' | 'Offline';
  latency?: number;
  className?: string;
}

/**
 * DataQualityIndicator - Critical for validating institutional data feeds.
 */
export function DataQualityIndicator({ status, latency, className }: DataQualityIndicatorProps) {
  return (
    <div className={cn(
      "inline-flex items-center gap-2 px-2.5 py-1 rounded-lg border text-[9px] font-black uppercase tracking-tighter",
      status === 'Optimal' && "bg-green/10 text-green border-green/20",
      status === 'Degraded' && "bg-amber/10 text-amber border-amber/20",
      status === 'Offline' && "bg-red/10 text-red border-red/20",
      className
    )}>
      {status === 'Optimal' && <ShieldCheck size={12} />}
      {status === 'Degraded' && <ShieldAlert size={12} />}
      {status === 'Offline' && <WifiOff size={12} />}
      
      <span>Feed {status}</span>
      
      {latency && (
        <>
          <div className="w-px h-2.5 bg-current opacity-20 mx-1" />
          <span className="font-mono">{latency}ms</span>
        </>
      )}
    </div>
  );
}
