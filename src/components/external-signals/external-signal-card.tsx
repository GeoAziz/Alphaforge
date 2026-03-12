'use client';

import { ExternalSignal } from '@/lib/types';
import { cn } from '@/lib/utils';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Badge } from '@/components/ui/badge';
import { Clock, ExternalLink, ShieldAlert, CheckCircle2, Ban, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';

interface ExternalSignalCardProps {
  signal: ExternalSignal;
}

export function ExternalSignalCard({ signal }: ExternalSignalCardProps) {
  const isRejected = signal.status === 'rejected';
  const isExecuted = signal.status === 'executed';

  return (
    <SpotlightCard className={cn(
      "p-6 border-border-subtle group transition-all",
      isRejected && "opacity-60 grayscale-[0.5]"
    )}>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-elevated flex items-center justify-center border border-border-subtle shadow-inner">
            <div className="text-[10px] font-black text-text-muted">TV</div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black tracking-tighter uppercase">{signal.asset}</span>
              <Badge variant="outline" className={cn(
                "text-[8px] font-black uppercase border-primary/20 text-primary",
                signal.direction === 'SHORT' && "text-red border-red/20"
              )}>
                {signal.direction}
              </Badge>
            </div>
            <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest flex items-center gap-2 mt-1">
              Source: {signal.source}
              <div className="w-1 h-1 rounded-full bg-border-subtle" />
              <span className="flex items-center gap-1"><Clock size={10} /> {format(new Date(signal.timestamp), 'HH:mm:ss')}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-8 lg:gap-12 items-center">
          <div className="space-y-1">
            <div className="text-[8px] font-black text-text-muted uppercase tracking-widest">Confidence</div>
            <div className={cn(
              "text-sm font-mono font-bold",
              (signal.confidence || 0) >= 70 ? "text-green" : "text-amber"
            )}>
              {signal.confidence}%
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-[8px] font-black text-text-muted uppercase tracking-widest">Sync Status</div>
            <div className="flex items-center gap-2">
              {isExecuted ? (
                <span className="text-[10px] font-black text-green uppercase flex items-center gap-1">
                  <CheckCircle2 size={12} /> Executed
                </span>
              ) : isRejected ? (
                <span className="text-[10px] font-black text-red uppercase flex items-center gap-1">
                  <Ban size={12} /> Rejected
                </span>
              ) : (
                <span className="text-[10px] font-black text-primary uppercase flex items-center gap-1">
                  <ShieldAlert size={12} /> Logged
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 md:col-span-1 col-span-2 border-t md:border-none pt-4 md:pt-0">
            {isRejected && (
              <span className="text-[9px] font-bold text-red uppercase mr-auto md:mr-0 line-clamp-1">{signal.rejectionReason}</span>
            )}
            <Button variant="ghost" size="sm" className="h-8 px-3 text-[9px] font-black uppercase gap-2 hover:bg-elevated">
              <Copy size={12} /> Copy Payload
            </Button>
            <Button variant="ghost" size="sm" className="h-8 px-3 text-[9px] font-black uppercase gap-2 hover:bg-elevated">
              <ExternalLink size={12} /> View Raw
            </Button>
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
