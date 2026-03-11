'use client';

import { useFirestore, useUser, useCollection, useDoc, useMemoFirebase, useAuth } from '@/firebase';
import { collection, query, orderBy, limit, doc } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { PriceTicker } from '@/components/shared/price-ticker';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { EmptyState } from '@/components/shared/empty-state';
import { SkeletonCard } from '@/components/shared/skeleton-card';
import { Skeleton } from '@/components/ui/skeleton';
import { initiateAnonymousSignIn } from '@/firebase/non-blocking-login';
import { 
  Activity, 
  TrendingUp, 
  Zap, 
  ArrowUpRight, 
  ArrowDownRight, 
  ShieldAlert,
  LayoutDashboard
} from 'lucide-react';
import { Signal, MarketTicker, PortfolioSummary } from '@/lib/types';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
  const { user, isUserLoading } = useUser();
  const { auth } = useAuth();
  const db = useFirestore();

  const tickersQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketTickers'), limit(6));
  }, [db, user]);

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'signals'), orderBy('createdAt', 'desc'), limit(4));
  }, [db, user]);

  const summaryRef = useMemoFirebase(() => {
    if (!db || !user) return null;
    return doc(db, 'users', user.uid, 'portfolioSummary', user.uid);
  }, [db, user]);

  const { data: tickers, isLoading: isTickersLoading } = useCollection<MarketTicker>(tickersQuery);
  const { data: signals, isLoading: isSignalsLoading } = useCollection<Signal>(signalsQuery);
  const { data: summary, isLoading: isSummaryLoading } = useDoc<PortfolioSummary>(summaryRef);

  if (!user && !isUserLoading) {
    return (
      <EmptyState 
        title="Handshake Required"
        description="AlphaForge institutional access is restricted to authorized entities. Please initialize a guest session or connect your node."
        icon={ShieldAlert}
        actionLabel="Initialize Session"
        onAction={() => initiateAnonymousSignIn(auth)}
      />
    );
  }

  return (
    <div className="p-6 lg:p-10 space-y-8 animate-in fade-in duration-700 pb-24 md:pb-10">
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-black uppercase tracking-tighter gradient-text">Intelligence Terminal</h1>
        <p className="text-text-secondary text-sm font-medium">Real-time algorithmic consensus and portfolio optimization.</p>
      </header>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Zap size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Portfolio Value</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter text-text-primary">
            {isSummaryLoading ? <Skeleton className="h-9 w-32" /> : <AnimatedCounter value={summary?.totalEquity || 0} prefix="$" decimals={2} />}
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
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Unrealized PnL</span>
          </div>
          <div className={cn(
            "text-3xl font-black font-mono tracking-tighter",
            (summary?.unrealizedPnl || 0) >= 0 ? "text-green" : "text-red"
          )}>
            {isSummaryLoading ? <Skeleton className="h-9 w-32" /> : (
              <AnimatedCounter 
                value={summary?.unrealizedPnl || 0} 
                prefix={(summary?.unrealizedPnl || 0) >= 0 ? '+$' : '-$'} 
                decimals={2} 
              />
            )}
          </div>
          <div className="mt-2 text-[10px] font-bold text-text-muted uppercase">
            Aggregated Across Clusters
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-green/10 text-green">
              <TrendingUp size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Active Signals</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter text-text-primary">
            {isSignalsLoading ? <Skeleton className="h-9 w-12" /> : <AnimatedCounter value={signals?.length || 0} />}
          </div>
          <div className="mt-2 text-[10px] font-bold text-primary flex items-center gap-1 uppercase">
            High Confidence Consensus
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-amber/10 text-amber">
              <LayoutDashboard size={20} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Risk Exposure</span>
          </div>
          <div className="text-3xl font-black font-mono tracking-tighter text-text-primary">
            {isSummaryLoading ? <Skeleton className="h-9 w-20" /> : <AnimatedCounter value={summary?.marginUsed || 0} suffix="%" />}
          </div>
          <div className="mt-2 text-[10px] font-bold text-text-muted uppercase">
            Balanced Regime
          </div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {isTickersLoading ? <SkeletonCard rows={6} /> : (
            <SpotlightCard className="p-8 h-full">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
                  <Activity size={16} className="text-primary" />
                  Market Depth Aggregator
                </h3>
                <Link href="/market-intelligence" className="text-[10px] font-black uppercase text-primary hover:underline">
                  Full Intel Cluster
                </Link>
              </div>
              <div className="space-y-4">
                {tickers?.length === 0 ? (
                  <div className="py-12 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                    Scanning market depth for authorized nodes...
                  </div>
                ) : tickers?.map((ticker) => (
                  <div key={ticker.id} className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle group hover:border-primary/50 transition-all">
                    <div className="flex items-center gap-4">
                      <div className="font-black text-lg tracking-tighter text-text-primary">{ticker.asset}</div>
                      <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">Vol: {(ticker.volume24h / 1000000).toFixed(1)}M</div>
                    </div>
                    <div className="flex items-center gap-8 text-right">
                      <PriceTicker initialPrice={ticker.price} className="text-lg" />
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
              </div>
            </SpotlightCard>
          )}
        </div>

        <div>
          {isSignalsLoading ? <SkeletonCard rows={4} /> : (
            <SpotlightCard className="p-8 h-full">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
                  <Zap size={16} className="text-accent" />
                  Alpha Stream
                </h3>
                <Link href="/signals" className="text-[10px] font-black uppercase text-accent hover:underline">
                  All Signals
                </Link>
              </div>
              <div className="space-y-4">
                {signals?.length === 0 ? (
                  <div className="py-12 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                    No active signals on current frequency.
                  </div>
                ) : signals?.map((signal) => (
                  <div key={signal.id} className="p-4 rounded-xl border border-border-subtle bg-elevated/10 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-black tracking-tight text-text-primary">{signal.asset}</span>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest",
                        signal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                      )}>
                        {signal.direction}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-bold">
                      <span className="text-text-muted uppercase">Confidence</span>
                      <span className="text-primary">{signal.confidence}%</span>
                    </div>
                    <div className="w-full bg-border-subtle h-1 rounded-full overflow-hidden">
                      <div 
                        className="bg-primary h-full transition-all duration-1000" 
                        style={{ width: `${signal.confidence}%` }} 
                      />
                    </div>
                  </div>
                ))}
              </div>
            </SpotlightCard>
          )}
        </div>
      </div>
    </div>
  );
}