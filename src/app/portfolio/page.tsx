'use client';

import { useFirestore, useUser, useCollection, useDoc, useMemoFirebase } from '@/firebase';
import { collection, doc, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { PriceTicker } from '@/components/shared/price-ticker';
import { Position, Trade, PortfolioSummary } from '@/lib/types';
import { 
  Wallet, 
  Briefcase, 
  History, 
  TrendingUp, 
  Activity, 
  Zap, 
  ArrowRight,
  Filter
} from 'lucide-react';
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
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export default function PortfolioPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [tradeFilter, setTradeFilter] = useState('all');

  const summaryRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid, 'portfolioSummary', user.uid);
  }, [user, db]);

  const positionsQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return collection(db, 'users', user.uid, 'positions');
  }, [user, db]);

  const tradesQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return query(collection(db, 'users', user.uid, 'trades'), orderBy('closedAt', 'desc'));
  }, [user, db]);

  const { data: summary, isLoading: isSummaryLoading } = useDoc<PortfolioSummary>(summaryRef);
  const { data: positions, isLoading: isPositionsLoading } = useCollection<Position>(positionsQuery);
  const { data: trades, isLoading: isTradesLoading } = useCollection<Trade>(tradesQuery);

  const filteredTrades = trades?.filter(t => {
    if (tradeFilter === 'all') return true;
    return t.status === tradeFilter;
  }) || [];

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Wallet size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Handshake Restricted</h2>
          <p className="text-sm text-text-muted leading-relaxed">Establish an institutional node connection to authorize access to real-time portfolio intelligence.</p>
          <Button className="w-full h-12 bg-primary text-primary-foreground font-black uppercase text-xs rounded-xl">Initialize Node Session</Button>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-8 pb-32 max-w-screen-2xl mx-auto animate-page pr-safe pl-safe">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Portfolio Intelligence</h1>
          <p className="text-muted-foreground text-sm font-medium">Real-time risk exposure and historical alpha verification.</p>
        </header>
        <div className="flex items-center gap-3">
          <div className="h-9 px-4 rounded-md border border-border-subtle bg-elevated/20 flex items-center gap-2 text-[10px] font-black uppercase text-green">
            <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
            Handshake Synced
          </div>
        </div>
      </div>

      {/* Hero Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <SpotlightCard className="p-6 border-primary/20 bg-primary/5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-[10px] font-black uppercase tracking-widest text-primary/70">Managed Equity</div>
            <Wallet size={14} className="text-primary/50" />
          </div>
          <div className="text-2xl lg:text-3xl font-black font-mono tracking-tighter">
            <AnimatedCounter value={summary?.totalEquity || 0} prefix="$" decimals={2} />
          </div>
          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 flex-1 bg-elevated rounded-full overflow-hidden">
              <div className="h-full bg-primary w-[75%]" />
            </div>
            <span className="text-[9px] font-black text-text-muted uppercase">75% Util</span>
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6 border-green/20">
          <div className="flex items-center justify-between mb-4">
            <div className="text-[10px] font-black uppercase tracking-widest text-green/70">Unrealized PnL</div>
            <TrendingUp size={14} className="text-green/50" />
          </div>
          <div className={cn(
            "text-2xl lg:text-3xl font-black font-mono tracking-tighter",
            (summary?.unrealizedPnl || 0) >= 0 ? "text-green" : "text-red"
          )}>
            <AnimatedCounter value={summary?.unrealizedPnl || 0} prefix={summary?.unrealizedPnl! >= 0 ? "+$" : "-$"} decimals={2} />
          </div>
          <div className="mt-4 text-[9px] font-bold text-text-muted uppercase flex items-center gap-1">
            <Activity size={10} /> Live Market Delta
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6 border-accent/20">
          <div className="flex items-center justify-between mb-4">
            <div className="text-[10px] font-black uppercase tracking-widest text-accent/70">Realized Perf</div>
            <Activity size={14} className="text-accent/50" />
          </div>
          <div className="text-2xl lg:text-3xl font-black font-mono tracking-tighter">
            <AnimatedCounter value={summary?.realizedPnl || 0} prefix="$" decimals={2} />
          </div>
          <div className="mt-4 text-[9px] font-bold text-text-muted uppercase">Session Alpha</div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="text-[10px] font-black uppercase tracking-widest text-text-muted">Active Clusters</div>
            <Zap size={14} className="text-amber/50" />
          </div>
          <div className="text-2xl lg:text-3xl font-black font-mono tracking-tighter">
            <AnimatedCounter value={summary?.openPositions || 0} />
          </div>
          <div className="mt-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
            <span className="text-[9px] font-black text-green uppercase tracking-widest">Live Nodes</span>
          </div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-12 gap-6 lg:gap-8">
        {/* Active Risk Table/List */}
        <div className="col-span-12 xl:col-span-8 space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <Briefcase size={16} className="text-primary" />
              Active Risk Exposure
            </h3>
            <Badge variant="outline" className="text-[9px] font-black uppercase border-primary/20 text-primary">Live Telemetry</Badge>
          </div>
          
          <div className="space-y-4">
            {isPositionsLoading ? (
              Array(3).fill(0).map((_, i) => (
                <div key={i} className="h-32 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
              ))
            ) : positions?.length === 0 ? (
              <SpotlightCard className="p-12 text-center border-dashed">
                <div className="text-[10px] font-black uppercase text-text-muted tracking-widest">No active terminal positions.</div>
              </SpotlightCard>
            ) : positions?.map((pos) => (
              <SpotlightCard key={pos.id} className="p-4 lg:p-6 group hover:border-primary/30 transition-all">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  <div className="flex items-center gap-4 lg:gap-6">
                    <div className={cn(
                      "w-10 h-10 lg:w-12 lg:h-12 rounded-xl flex items-center justify-center font-black text-[10px] lg:text-xs uppercase",
                      pos.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                    )}>
                      {pos.direction}
                    </div>
                    <div>
                      <div className="text-xl lg:text-2xl font-black tracking-tighter">{pos.asset}</div>
                      <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest flex items-center gap-2">
                        {pos.quantity} Units
                        <div className="w-1 h-1 rounded-full bg-border-subtle" />
                        Opened: {new Date(pos.openedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-12 text-left lg:text-right border-t lg:border-none pt-4 lg:pt-0">
                    <div>
                      <div className="text-[8px] lg:text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">Entry</div>
                      <div className="text-xs lg:text-sm font-mono font-bold">${pos.entryPrice.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-[8px] lg:text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">Live Tick</div>
                      <PriceTicker initialPrice={pos.currentPrice} className="text-xs lg:text-sm p-0 min-w-0 border-none bg-transparent" />
                    </div>
                    <div>
                      <div className="text-[8px] lg:text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">Unrealized</div>
                      <div className={cn(
                        "text-xs lg:text-sm font-mono font-bold",
                        pos.unrealizedPnl >= 0 ? "text-green" : "text-red"
                      )}>
                        {pos.unrealizedPnl >= 0 ? '+' : ''}{pos.unrealizedPnl.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[8px] lg:text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">Exposure</div>
                      <div className="text-xs lg:text-sm font-mono font-bold text-primary">{pos.riskExposure}%</div>
                    </div>
                  </div>
                </div>
              </SpotlightCard>
            ))}
          </div>
        </div>

        {/* Trade Ledger - Mobile Card View / Desktop Table */}
        <div className="col-span-12 xl:col-span-4 space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <History size={16} className="text-accent" />
              Terminal Ledger
            </h3>
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setTradeFilter('all')}
                className={cn("h-6 px-2 text-[8px] font-black uppercase rounded-md touch-target", tradeFilter === 'all' ? "bg-accent/10 text-accent" : "text-text-muted")}
              >All</Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setTradeFilter('win')}
                className={cn("h-6 px-2 text-[8px] font-black uppercase rounded-md touch-target", tradeFilter === 'win' ? "bg-green/10 text-green" : "text-text-muted")}
              >Wins</Button>
            </div>
          </div>

          <SpotlightCard className="p-0 overflow-hidden border-border-subtle bg-surface/30 backdrop-blur-md">
            {/* Desktop Table */}
            <div className="hidden sm:block">
              <Table>
                <TableHeader className="bg-elevated/50">
                  <TableRow className="border-border-subtle hover:bg-transparent">
                    <TableHead className="text-[10px] font-black uppercase tracking-widest">Asset / Strategy</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-right">Outcome</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isTradesLoading ? (
                    Array(5).fill(0).map((_, i) => (
                      <TableRow key={i} className="border-border-subtle">
                        <TableCell colSpan={2} className="h-16 animate-pulse bg-elevated/10" />
                      </TableRow>
                    ))
                  ) : filteredTrades.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={2} className="h-32 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                        Scanning archive ledger...
                      </TableCell>
                    </TableRow>
                  ) : filteredTrades.map((trade) => (
                    <TableRow key={trade.id} className="border-border-subtle hover:bg-elevated/20 group transition-all cursor-default">
                      <TableCell className="py-4 relative">
                        <div className={cn(
                          "absolute left-0 top-0 bottom-0 w-1",
                          trade.status === 'win' ? "bg-green/40 shadow-[0_0_10px_rgba(52,211,153,0.3)]" : "bg-red/40"
                        )} />
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center font-black text-[9px] uppercase",
                            trade.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                          )}>
                            {trade.direction[0]}
                          </div>
                          <div>
                            <div className="font-black text-sm tracking-tight">{trade.asset}</div>
                            <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest">{trade.strategy}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className={cn(
                          "font-mono font-black text-sm",
                          trade.status === 'win' ? "text-green" : "text-red"
                        )}>
                          {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                        </div>
                        <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest">
                          {trade.pnlPercent.toFixed(2)}% ROI
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Mobile Card List */}
            <div className="sm:hidden divide-y divide-border-subtle">
              {filteredTrades.map((trade) => (
                <div key={trade.id} className="p-4 flex items-center justify-between hover:bg-elevated/10 relative">
                  <div className={cn(
                    "absolute left-0 top-0 bottom-0 w-1",
                    trade.status === 'win' ? "bg-green/40" : "bg-red/40"
                  )} />
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center font-black text-[9px] uppercase",
                      trade.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                    )}>
                      {trade.direction[0]}
                    </div>
                    <div>
                      <div className="font-black text-sm">{trade.asset}</div>
                      <div className="text-[8px] font-bold text-text-muted uppercase">{trade.strategy}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn(
                      "font-mono font-black text-sm",
                      trade.status === 'win' ? "text-green" : "text-red"
                    )}>
                      {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                    </div>
                    <div className="text-[8px] font-bold text-text-muted uppercase">
                      {trade.pnlPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-border-subtle bg-elevated/10 flex justify-between items-center">
              <span className="text-[9px] font-black uppercase text-text-muted">Archive Sequence</span>
              <Button variant="ghost" size="sm" className="h-6 px-3 text-[9px] font-black uppercase text-primary gap-1 group touch-target">
                Full Ledger <ArrowRight size={10} className="group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
          </SpotlightCard>
        </div>
      </div>
    </div>
  );
}
