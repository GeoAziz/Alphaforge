
'use client';

import { useFirestore, useUser, useCollection, useDoc, useMemoFirebase } from '@/firebase';
import { collection, doc, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { Position, Trade, PortfolioSummary } from '@/lib/types';
import { Wallet, ArrowUpRight, ArrowDownRight, Briefcase, History, TrendingUp, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from '@/components/ui/badge';

export default function PortfolioPage() {
  const { user } = useUser();
  const db = useFirestore();

  const summaryRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid, 'portfolio_summary', 'current');
  }, [user, db]);

  const positionsQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return collection(db, 'users', user.uid, 'positions');
  }, [user, db]);

  const tradesQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return query(collection(db, 'users', user.uid, 'trades'), orderBy('closedAt', 'desc'));
  }, [user, db]);

  const { data: summary } = useDoc<PortfolioSummary>(summaryRef);
  const { data: positions, isLoading: isPositionsLoading } = useCollection<Position>(positionsQuery);
  const { data: trades, isLoading: isTradesLoading } = useCollection<Trade>(tradesQuery);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Wallet size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Portfolio Access Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to view institutional-grade portfolio intelligence and active positions.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Portfolio Intelligence</h1>
        <p className="text-muted-foreground text-sm">Real-time performance metrics and active risk exposure.</p>
      </header>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SpotlightCard className="p-8 border-primary/20 bg-primary/5">
          <div className="text-[10px] font-black uppercase tracking-widest text-primary/70 mb-2">Total Equity</div>
          <div className="text-4xl font-black font-mono">
            <AnimatedCounter value={summary?.totalEquity || 0} prefix="$" decimals={2} />
          </div>
          <div className="flex items-center gap-2 mt-4">
             <div className={cn(
               "text-xs font-bold flex items-center gap-1",
               (summary?.unrealizedPnl || 0) >= 0 ? "text-green" : "text-red"
             )}>
               {(summary?.unrealizedPnl || 0) >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
               <AnimatedCounter value={Math.abs(summary?.unrealizedPnl || 0)} prefix="$" decimals={2} />
             </div>
             <span className="text-[10px] text-text-muted uppercase font-bold">Unrealized PnL</span>
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-8">
          <div className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Open Positions</div>
          <div className="text-4xl font-black font-mono">
            <AnimatedCounter value={summary?.openPositions || 0} />
          </div>
          <div className="mt-4 flex gap-4">
            <div>
              <div className="text-[10px] font-bold text-text-muted uppercase">Margin Used</div>
              <div className="text-sm font-mono font-bold">
                <AnimatedCounter value={summary?.marginUsed || 0} prefix="$" />
              </div>
            </div>
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-8">
          <div className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Total Trades</div>
          <div className="text-4xl font-black font-mono">
            <AnimatedCounter value={summary?.totalTrades || 0} />
          </div>
          <div className="mt-4 flex gap-4">
            <div>
              <div className="text-[10px] font-bold text-text-muted uppercase">Realized PnL</div>
              <div className={cn("text-sm font-mono font-bold", (summary?.realizedPnl || 0) >= 0 ? "text-green" : "text-red")}>
                <AnimatedCounter value={summary?.realizedPnl || 0} prefix="$" decimals={2} />
              </div>
            </div>
          </div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Active Positions */}
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <Briefcase size={16} />
              Active Risk
            </h3>
            <Badge variant="outline" className="text-[10px] font-black uppercase">Live</Badge>
          </div>
          <div className="grid gap-4">
            {isPositionsLoading ? (
              <div className="h-32 rounded-2xl bg-elevated/20 animate-pulse" />
            ) : positions?.length === 0 ? (
              <SpotlightCard className="p-12 text-center text-text-muted text-sm border-dashed">
                No active positions detected in current terminal cluster.
              </SpotlightCard>
            ) : positions?.map((pos) => (
              <SpotlightCard key={pos.id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-black uppercase",
                      pos.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                    )}>
                      {pos.direction}
                    </div>
                    <div className="text-xl font-black">{pos.asset}</div>
                  </div>
                  <div className="text-right">
                    <div className={cn(
                      "text-lg font-black font-mono",
                      pos.unrealizedPnl >= 0 ? "text-green" : "text-red"
                    )}>
                      {pos.unrealizedPnl >= 0 ? '+' : ''}{pos.unrealizedPnl.toFixed(2)}
                    </div>
                    <div className="text-[10px] font-bold text-text-muted uppercase">{pos.unrealizedPnlPercent.toFixed(2)}% ROI</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 border-t border-border-subtle pt-4">
                  <div>
                    <div className="text-[9px] text-text-muted uppercase font-black">Entry</div>
                    <div className="text-xs font-mono font-bold">${pos.entryPrice.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[9px] text-text-muted uppercase font-black">Current</div>
                    <div className="text-xs font-mono font-bold">${pos.currentPrice.toLocaleString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] text-text-muted uppercase font-black">Exposure</div>
                    <div className="text-xs font-mono font-bold text-primary">{pos.riskExposure}%</div>
                  </div>
                </div>
              </SpotlightCard>
            ))}
          </div>
        </div>

        {/* Recent Trades */}
        <div className="col-span-12 lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <History size={16} />
              Recent History
            </h3>
          </div>
          <SpotlightCard className="overflow-hidden">
            <Table>
              <TableHeader className="bg-elevated/50">
                <TableRow className="border-border-subtle hover:bg-transparent">
                  <TableHead className="text-[10px] font-black uppercase">Asset</TableHead>
                  <TableHead className="text-[10px] font-black uppercase">Direction</TableHead>
                  <TableHead className="text-[10px] font-black uppercase text-right">Outcome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades?.map((trade) => (
                  <TableRow key={trade.id} className="border-border-subtle hover:bg-elevated/20 group">
                    <TableCell className="font-bold py-4">
                      {trade.asset}
                      <div className="text-[9px] text-text-muted font-normal uppercase">
                        {new Date(trade.closedAt).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                       <span className={cn(
                         "text-[9px] font-black uppercase px-1.5 py-0.5 rounded",
                         trade.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                       )}>
                         {trade.direction}
                       </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className={cn(
                        "font-mono font-black",
                        trade.status === 'win' ? "text-green" : "text-red"
                      )}>
                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                      </div>
                      <div className="text-[9px] text-text-muted uppercase font-bold">
                        {trade.pnlPercent.toFixed(2)}%
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {(!trades || trades.length === 0) && !isTradesLoading && (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8 text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                      Scanning archive frequency...
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </SpotlightCard>
        </div>
      </div>
    </div>
  );
}
