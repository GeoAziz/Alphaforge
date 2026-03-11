'use client';

import { useFirestore, useUser, useCollection, useDoc, useMemoFirebase } from '@/firebase';
import { collection, query, orderBy, limit, doc } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { 
  Activity, 
  TrendingUp, 
  Zap, 
  ArrowUpRight, 
  ArrowDownRight, 
  LayoutDashboard,
  ShieldAlert
} from 'lucide-react';
import { Signal, MarketTicker, PortfolioSummary } from '@/lib/types';
import { cn } from '@/lib/utils';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useUser();
  const db = useFirestore();

  const tickersQuery = useMemoFirebase(() => {
    if (!db) return null;
    return query(collection(db, 'marketTickers'), limit(6));
  }, [db]);

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'signals'), orderBy('createdAt', 'desc'), limit(4));
  }, [db, user]);

  const summaryRef = useMemoFirebase(() => {
    if (!db || !user) return null;
    return doc(db, 'users', user.uid, 'portfolioSummary', user.uid);
  }, [db, user]);

  const { data: tickers } = useCollection<MarketTicker>(tickersQuery);
  const { data: signals } = useCollection<Signal>(signalsQuery);
  const { data: summary } = useDoc<PortfolioSummary>(summaryRef);

  if (!user) return <AuthPlaceholder />;

  return (
    <div className="p-6 lg:p-10 space-y-8 animate-in fade-in duration-700">
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-black uppercase tracking-tighter gradient-text">Intelligence Terminal</h1>
        <p className="text-muted-foreground text-sm font-medium">Real-time algorithmic consensus and portfolio optimization.</p>
      </header>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Zap size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Portfolio Value</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter">
            $<AnimatedCounter value={summary?.totalEquity || 0} decimals={2} />
          </div>
          <div className="mt-2 text-[10px] font-bold text-green flex items-center gap-1 uppercase">
            <TrendingUp size={12} /> Institutional Alpha: +12.4%
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <Activity size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Unrealized PnL</span>
          </div>
          <div className={cn(
            "text-3xl font-black font-mono tracking-tighter",
            (summary?.unrealizedPnl || 0) >= 0 ? "text-green" : "text-red"
          )}>
            {(summary?.unrealizedPnl || 0) >= 0 ? '+' : ''}
            $<AnimatedCounter value={Math.abs(summary?.unrealizedPnl || 0)} decimals={2} />
          </div>
          <div className="mt-2 text-[10px] font-bold text-muted-foreground uppercase">
            Aggregated Across 12 Clusters
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-green/10 text-green">
              <TrendingUp size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Active Signals</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter">
            <AnimatedCounter value={signals?.length || 0} />
          </div>
          <div className="mt-2 text-[10px] font-bold text-primary flex items-center gap-1 uppercase">
            High Confidence Consensus
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
              <LayoutDashboard size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Risk Exposure</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter">
            <AnimatedCounter value={summary?.marginUsed || 0} />%
          </div>
          <div className="mt-2 text-[10px] font-bold text-muted-foreground uppercase">
            Balanced Regime
          </div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Overview */}
        <SpotlightCard className="lg:col-span-2 p-8">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
              <Activity size={16} className="text-primary" />
              Market Depth Aggregator
            </h3>
            <Link href="/market-intelligence" className="text-[10px] font-black uppercase text-primary hover:underline">
              Full Intel Cluster
            </Link>
          </div>
          <div className="space-y-4">
            {tickers?.map((ticker) => (
              <div key={ticker.id} className="flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border-subtle group hover:border-primary/50 transition-all">
                <div className="flex items-center gap-4">
                  <div className="font-black text-lg tracking-tighter">{ticker.asset}</div>
                  <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Vol: {(ticker.volume24h / 1000000).toFixed(1)}M</div>
                </div>
                <div className="flex items-center gap-8 text-right">
                  <div className="font-mono font-bold">${ticker.price.toLocaleString()}</div>
                  <div className={cn(
                    "text-xs font-black flex items-center gap-1 min-w-[60px] justify-end",
                    ticker.change24h >= 0 ? "text-green" : "text-red"
                  )}>
                    {ticker.change24h >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {ticker.change24h}%
                  </div>
                </div>
              </div>
            ))}
            {!tickers && <div className="text-center p-12 text-muted-foreground animate-pulse">Synchronizing market clusters...</div>}
          </div>
        </SpotlightCard>

        {/* Recent Signals */}
        <SpotlightCard className="p-8">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
              <Zap size={16} className="text-accent" />
              Alpha Stream
            </h3>
            <Link href="/signals" className="text-[10px] font-black uppercase text-accent hover:underline">
              All Signals
            </Link>
          </div>
          <div className="space-y-4">
            {signals?.map((signal) => (
              <div key={signal.id} className="p-4 rounded-xl border border-border-subtle bg-muted/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-black tracking-tight">{signal.asset}</span>
                  <span className={cn(
                    "px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest",
                    signal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                  )}>
                    {signal.direction}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold">
                  <span className="text-muted-foreground uppercase">Confidence</span>
                  <span className="text-primary">{signal.confidence}%</span>
                </div>
                <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                  <div 
                    className="bg-primary h-full transition-all duration-1000" 
                    style={{ width: `${signal.confidence}%` }} 
                  />
                </div>
              </div>
            ))}
            {!signals && <div className="text-center p-12 text-muted-foreground animate-pulse">Scanning signal arrays...</div>}
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

function AuthPlaceholder() {
  return (
    <div className="h-[80vh] flex items-center justify-center p-6">
      <SpotlightCard className="max-w-md w-full p-12 text-center space-y-6">
        <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          <ShieldAlert size={32} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-black uppercase tracking-tighter">Handshake Required</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            AlphaForge institutional access is restricted to authorized entities. Please initialize a guest session or connect your node.
          </p>
        </div>
        <button className="w-full h-12 bg-primary text-primary-foreground font-black uppercase text-xs tracking-widest rounded-lg hover:opacity-90 transition-opacity">
          Initialize Session
        </button>
      </SpotlightCard>
    </div>
  );
}