
'use client';

import { AuditLogEntry } from "@/lib/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

interface AuditTrailProps {
  logs: AuditLogEntry[];
}

/**
 * AuditTrail - Read-only immutable log viewer for terminal telemetry.
 */
export function AuditTrail({ logs }: AuditTrailProps) {
  return (
    <div className="rounded-xl border border-border-subtle overflow-hidden">
      <Table>
        <TableHeader className="bg-elevated/50">
          <TableRow className="border-border-subtle hover:bg-transparent">
            <TableHead className="text-[9px] font-black uppercase text-text-muted">Timestamp</TableHead>
            <TableHead className="text-[9px] font-black uppercase text-text-muted">Action Node</TableHead>
            <TableHead className="text-[9px] font-black uppercase text-text-muted text-right">Verification</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.map((log) => (
            <TableRow key={log.id} className="border-border-subtle hover:bg-elevated/20 group transition-colors">
              <TableCell className="font-mono text-[9px] text-text-muted py-3">
                {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
              </TableCell>
              <TableCell className="font-black text-[10px] uppercase tracking-tighter">
                {log.action}
                <div className="text-[8px] font-bold text-text-muted opacity-50">{log.node}</div>
              </TableCell>
              <TableCell className="text-right">
                <Badge variant="outline" className={cn(
                  "text-[8px] font-black uppercase tracking-widest px-2 py-0 h-5",
                  log.status === 'Success' ? "border-green/30 text-green" : 
                  log.status === 'Warning' ? "border-amber/30 text-amber" : "border-red/30 text-red"
                )}>
                  {log.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
