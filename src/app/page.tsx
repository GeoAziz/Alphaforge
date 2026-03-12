'use client';

import { useEffect, useState } from 'react';
import { useUser, useFirestore, useDoc, useMemoFirebase, useAuth } from '@/firebase';
import { doc } from 'firebase/firestore';
import { HeroSection } from '@/components/dashboard/hero-section';
import { PerformanceSummary } from '@/components/dashboard/performance-summary';
import { MarketOverview } from '@/components/dashboard/market-overview';
import { MarketHeatmap } from '@/components/dashboard/market-heatmap';
import { AlphaStream } from '@/components/dashboard/alpha-stream';
import { MarketSentimentCell } from '@/components/dashboard/market-sentiment';
import { QuickAlerts } from '@/components/dashboard/quick-alerts';
import { ShieldAlert, Loader2 } from 'lucide-react';
import { PortfolioSummary } from '@/lib/types';
import { EmptyState } from '@/components/shared/empty-state';
import { initiateAnonymousSignIn } from '@/firebase/non-blocking-login';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { user, isUserLoading } = useUser();
  const { auth } = useAuth();
  const db = useFirestore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const summaryRef = useMemoFirebase(() => {
    if (!db || !user) return null;
    return doc(db, 'users', user.uid, 'portfolioSummary', user.uid);
  }, [db, user]);

  const { data: summary, isLoading: isSummaryLoading } = useDoc<PortfolioSummary>(summaryRef);

  if (isUserLoading) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!user) {
    return (
      <EmptyState 
        title="Institutional Handshake Required"
        description="AlphaForge access is restricted to authorized entities. Please initialize a guest node session or connect your institutional credentials."
        icon={ShieldAlert}
        actionLabel="Initialize Node Session"
        onAction={() => initiateAnonymousSignIn(auth)}
      />
    );
  }

  return (
    <div className={cn(
      "p-6 lg:p-8 space-y-8 pb-24 md:pb-10 transition-all duration-1000 ease-out-custom",
      mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
    )}>
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-black uppercase tracking-tighter gradient-text leading-none">Intelligence Terminal</h1>
        <p className="text-text-secondary text-sm font-medium tracking-tight">Real-time algorithmic consensus and portfolio optimization cluster.</p>
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

        {/* Alpha Stream: Stagger 400ms */}
        <div className={cn(
          "col-span-12 md:col-span-6 xl:col-span-4 transition-all duration-700 delay-400",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <AlphaStream />
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
          "col-span-12 transition-all duration-700 delay-600",
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        )}>
          <MarketHeatmap />
        </div>
      </div>
    </div>
  );
}
