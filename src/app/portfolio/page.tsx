'use client';

import { useFirestore, useUser, useCollection, useDoc, useMemoFirebase } from '@/firebase';
import { collection, doc, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { Position, Trade, PortfolioSummary } from '@/lib/types';
import { 
  Wallet, 
  TrendingUp, 
  Activity, 
  Zap, 
  ShieldAlert
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ActivePositions } from '@/components/portfolio/active-positions';
import { TradeHistory } from '@/components/portfolio/trade-history';

export default function PortfolioPage() {
  const { user } = useUser();
  const db = useFirestore();

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
    <div className="p-8 space-y-8 pb-24 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Portfolio Intelligence</h1>
        <p className="text-muted-foreground text-sm font-medium">Real-time performance metrics and active risk exposure.</p>
      </header>

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

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8">
          <ActivePositions positions={positions} isLoading={isPositionsLoading} />
        </div>
        <div className="col-span-12 lg:col-span-4">
          <TradeHistory trades={trades} isLoading={isTradesLoading} />
        </div>
      </div>
    </div>
  );
}
