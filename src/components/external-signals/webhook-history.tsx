'use client';

import { WebhookEvent } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Activity, ShieldCheck, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface WebhookHistoryProps {
  events: WebhookEvent[];
  isLoading?: boolean;
}

export function WebhookHistory({ events, isLoading }: WebhookHistoryProps) {
  return (
    <SpotlightCard className="p-0 overflow-hidden border-border-subtle bg-surface/30">
      <div className="p-6 border-b border-border-subtle bg-elevated/20 flex justify-between items-center">
        <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
          <Activity size={16} className="text-primary" />
          Webhook Activity — Last 24H
        </h3>
        <span className="text-[9px] font-black uppercase text-text-muted">Live Sync</span>
      </div>
      
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-elevated/50">
            <TableRow className="border-border-subtle hover:bg-transparent">
              <TableHead className="text-[9px] font-black uppercase tracking-widest">Timestamp</TableHead>
              <TableHead className="text-[9px] font-black uppercase tracking-widest">Source IP</TableHead>
              <TableHead className="text-[9px] font-black uppercase tracking-widest">Status</TableHead>
              <TableHead className="text-[9px] font-black uppercase tracking-widest text-right">Verification</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array(3).fill(0).map((_, i) => (
                <TableRow key={i} className="border-border-subtle">
                  <TableCell colSpan={4} className="h-12 animate-pulse bg-elevated/10" />
                </TableRow>
              ))
            ) : events.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                  Monitoring ingest socket...
                </TableCell>
              </TableRow>
            ) : events.map((event) => (
              <TableRow key={event.id} className="border-border-subtle hover:bg-elevated/20 transition-colors">
                <TableCell className="font-mono text-[10px] text-text-secondary py-4">
                  {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
                </TableCell>
                <TableCell className="text-[10px] font-mono font-bold text-text-muted">
                  {event.sourceIp || "Unknown"}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(
                    "text-[8px] font-black uppercase px-2 h-5",
                    event.processingStatus === 'processed' ? "text-green border-green/20" : "text-red border-red/20"
                  )}>
                    {event.processingStatus}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className={cn(
                    "inline-flex items-center gap-1.5 text-[9px] font-black uppercase",
                    event.signatureValid ? "text-green" : "text-red"
                  )}>
                    {event.signatureValid ? <ShieldCheck size={12} /> : <AlertCircle size={12} />}
                    {event.signatureValid ? "Verified" : "Invalid Signature"}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </SpotlightCard>
  );
}
