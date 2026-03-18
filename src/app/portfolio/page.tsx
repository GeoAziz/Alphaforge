'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useCollection, useDoc, useMemoFirebase } from '@/firebase';
// import { collection, doc, query, orderBy } from 'firebase/firestore';
import { api } from '@/lib/api';
import { useAnalytics } from '@/providers/posthog-provider';
import { useWebSocket } from '@/hooks/use-websocket';
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
  const analytics = useAnalytics();
  const { isConnected: marketConnected } = useWebSocket('/ws/market-updates');
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);
  const [isPositionsLoading, setIsPositionsLoading] = useState(true);
  const [isTradesLoading, setIsTradesLoading] = useState(true);

  useEffect(() => {
    analytics.pageView('/portfolio');
    const uid = user?.uid || 'mock-user-001';
    api.portfolio.getSummary(uid).then(d => { setSummary(d); setIsSummaryLoading(false); });
    api.portfolio.getPositions(uid).then(d => { setPositions(d); setIsPositionsLoading(false); });
    api.portfolio.getTrades(uid).then(d => { setTrades(d); setIsTradesLoading(false); });
  }, [user, analytics]);

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
