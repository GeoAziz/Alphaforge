'use client';

import { Trade } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { History, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface TradeHistoryProps {
  trades: Trade[] | null;
  isLoading: boolean;
}

/**
 * TradeHistory - The institutional ledger of resolved node signals.
 */
export function TradeHistory({ trades, isLoading }: TradeHistoryProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
          <History size={16} className="text-accent" />
          Terminal Ledger
        </h3>
        <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Resolved Resolutions</span>
      </div>

      <SpotlightCard className="p-0 overflow-hidden border-border-subtle bg-surface/30">
        <Table>
          <TableHeader className="bg-elevated/50">
            <TableRow className="border-border-subtle hover:bg-transparent">
              <TableHead className="text-[10px] font-black uppercase tracking-widest">Asset / Strategy</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest">Entry / Exit</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest text-right">Alpha Delta</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest text-right hidden lg:table-cell">Resolution Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array(5).fill(0).map((_, i) => (
                <TableRow key={i} className="border-border-subtle">
                  <TableCell colSpan={4} className="h-16 animate-pulse bg-elevated/10" />
                </TableRow>
              ))
            ) : !trades || trades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                  Scanning archive ledger nodes...
                </TableCell>
              </TableRow>
            ) : (
              trades.map((trade) => (
                <TableRow key={trade.id} className="border-border-subtle hover:bg-elevated/20 group transition-all">
                  <TableCell className="py-4 relative">
                    <div className={cn(
                      "absolute left-0 top-0 bottom-0 w-1",
                      trade.status === 'win' ? "bg-green/40 shadow-[0_0_10px_rgba(52,211,153,0.3)]" : "bg-red/40 shadow-[0_0_10px_rgba(248,113,113,0.3)]"
                    )} />
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center font-black text-[9px] uppercase",
                        trade.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                      )}>
                        {trade.direction[0]}
                      </div>
                      <div>
                        <div className="font-black text-sm tracking-tight uppercase">{trade.asset}</div>
                        <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">{trade.strategy}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-[10px] font-mono font-bold text-text-secondary leading-tight">
                      IN: ${trade.entryPrice.toLocaleString()}
                    </div>
                    <div className="text-[10px] font-mono font-bold text-text-muted leading-tight">
                      OUT: ${trade.exitPrice.toLocaleString()}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className={cn(
                      "font-mono font-black text-sm",
                      trade.status === 'win' ? "text-green" : "text-red"
                    )}>
                      {trade.status === 'win' ? <TrendingUp size={12} className="inline mr-1" /> : <TrendingDown size={12} className="inline mr-1" />}
                      {trade.pnlPercent.toFixed(2)}%
                    </div>
                    <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest">
                      ${trade.pnl.toLocaleString()} Profit
                    </div>
                  </TableCell>
                  <TableCell className="text-right hidden lg:table-cell">
                    <div className="text-[10px] font-bold text-text-secondary uppercase">
                      {format(new Date(trade.closedAt), 'MMM dd, HH:mm')}
                    </div>
                    <div className="text-[8px] font-black text-text-muted uppercase tracking-tighter">
                      Alpha Anchored
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </SpotlightCard>
    </div>
  );
}
