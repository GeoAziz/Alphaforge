'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useDoc, useMemoFirebase, useAuth } from '@/firebase';
// import { doc } from 'firebase/firestore';
// import { initiateAnonymousSignIn } from '@/firebase/non-blocking-login';
import { api } from '@/lib/api';
import { useAnalytics } from '@/providers/posthog-provider';
import { useWebSocket } from '@/hooks/use-websocket';
import { HeroSection } from '@/components/dashboard/hero-section';
import { PerformanceSummary } from '@/components/dashboard/performance-summary';
import { MarketOverview } from '@/components/dashboard/market-overview';
import { MarketHeatmap } from '@/components/dashboard/market-heatmap';
import { ActiveSignalsPanel } from '@/components/dashboard/active-signals-panel';
import { MarketSentimentCell } from '@/components/dashboard/market-sentiment';
import { QuickAlerts } from '@/components/dashboard/quick-alerts';
import { RecentSignals } from '@/components/dashboard/recent-signals';
import { PortfolioSummary } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { user } = useUser();
  const analytics = useAnalytics();
  const { isConnected: marketConnected } = useWebSocket('/ws/market-updates');
  const { isConnected: signalsConnected } = useWebSocket('/ws/signals');
  const [mounted, setMounted] = useState(false);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
    
    // Track dashboard view
    analytics.pageView('/dashboard');
    
    // Use actual user ID if authenticated, fallback to demo ID
    const userId = user?.uid || 'demo-user-001';
    
    api.portfolio.getSummary(userId).then(data => {
      setSummary(data);
      setIsSummaryLoading(false);
    }).catch(error => {
      console.error('Failed to load portfolio summary:', error);
      setIsSummaryLoading(false);
    });
  }, [user?.uid, analytics]);

  return (
    <div className={cn(
      "p-6 lg:p-8 space-y-8 pb-24 md:pb-10 animate-page",
      mounted && "opacity-100"
    )}>
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-black uppercase tracking-tighter gradient-text leading-none">Intelligence Terminal</h1>
        <p className="text-text-secondary text-sm font-medium tracking-tight">
          Real-time algorithmic consensus and portfolio optimization cluster.
          {marketConnected && signalsConnected && <span className="text-green-500"> • Live</span>}
          {(!marketConnected || !signalsConnected) && <span className="text-amber-600"> • Connecting...</span>}
        </p>
      </header>

      {/* Institutional 12-Column Asymmetric Bento Grid */}
      <div className="grid grid-cols-12 gap-6 auto-rows-[minmax(180px,auto)]">
        
        {/* Hero Section: Stagger 0ms */}
        <div className={cn(
          "col-span-12 xl:col-span-4 xl:row-span-2 transition-all duration-700",
          mounted ? "opacity-100 scale-100" : "opacity-0 scale-95"
        )}>
          <HeroSection summary={summary} isLoading={isSummaryLoading} />
        </div>

        {/* Performance Summary Stats: Stagger 100ms */}
        <div className={cn(
          "col-span-12 xl:col-span-8 transition-all duration-700 delay-100",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <PerformanceSummary summary={summary} isLoading={isSummaryLoading} />
        </div>

        {/* Market Overview: Stagger 200ms */}
        <div className={cn(
          "col-span-12 xl:col-span-8 transition-all duration-700 delay-200",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <MarketOverview />
        </div>

        {/* Market Sentiment Cell: Stagger 300ms */}
        <div className={cn(
          "col-span-12 md:col-span-6 xl:col-span-4 transition-all duration-700 delay-300",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <MarketSentimentCell />
        </div>

        {/* Active Signals Node: Stagger 400ms */}
        <div className={cn(
          "col-span-12 md:col-span-6 xl:col-span-4 transition-all duration-700 delay-400",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <ActiveSignalsPanel />
        </div>

        {/* Quick Alerts Node: Stagger 500ms */}
        <div className={cn(
          "col-span-12 md:col-span-6 xl:col-span-4 transition-all duration-700 delay-500",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <QuickAlerts />
        </div>

        {/* Market Heatmap: Stagger 600ms */}
        <div className={cn(
          "col-span-12 xl:col-span-8 transition-all duration-700 delay-600",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <MarketHeatmap />
        </div>

        {/* Recent Signals Resolution Node: Stagger 700ms */}
        <div className={cn(
          "col-span-12 xl:col-span-4 transition-all duration-700 delay-700",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <RecentSignals />
        </div>
      </div>
    </div>
  );
}
