'use client';

import { Position } from '@/lib/types';
import { cn } from '@/lib/utils';
import { PriceTicker } from '@/components/shared/price-ticker';
import { TableCell, TableRow } from '@/components/ui/table';

interface PositionRowProps {
  position: Position;
}

/**
 * PositionRow - Individual telemetry row for active terminal nodes.
 */
export function PositionRow({ position }: PositionRowProps) {
  return (
    <TableRow className="border-border-subtle hover:bg-elevated/20 group transition-all cursor-default">
      <TableCell className="py-4 relative">
        <div className={cn(
          "absolute left-0 top-0 bottom-0 w-1",
          position.direction === 'LONG' ? "bg-green/40 shadow-[0_0_10px_rgba(52,211,153,0.3)]" : "bg-red/40 shadow-[0_0_10px_rgba(248,113,113,0.3)]"
        )} />
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center font-black text-[9px] uppercase",
            position.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
          )}>
            {position.direction[0]}
          </div>
          <div>
            <div className="font-black text-sm tracking-tight uppercase">{position.asset}</div>
            <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">
              Opened {new Date(position.openedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      </TableCell>
      <TableCell className="font-mono text-xs font-bold">
        ${position.entryPrice.toLocaleString()}
      </TableCell>
      <TableCell>
        <PriceTicker initialPrice={position.currentPrice} className="text-xs p-0 min-w-0 border-none bg-transparent" />
      </TableCell>
      <TableCell className="text-right">
        <div className={cn(
          "font-mono font-black text-xs",
          position.unrealizedPnl >= 0 ? "text-green" : "text-red"
        )}>
          {position.unrealizedPnl >= 0 ? '+' : ''}{position.unrealizedPnl.toFixed(2)}
        </div>
        <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest">
          {position.unrealizedPnlPercent.toFixed(2)}%
        </div>
      </TableCell>
      <TableCell className="text-right hidden md:table-cell">
        <div className="flex flex-col items-end gap-1.5">
          <div className="text-[9px] font-black text-primary uppercase">{position.riskExposure}%</div>
          <div className="h-1 w-16 bg-elevated rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary" 
              style={{ width: `${position.riskExposure * 10}%` }} 
            />
          </div>
        </div>
      </TableCell>
    </TableRow>
  );
}
