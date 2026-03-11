
'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useDoc, useMemoFirebase, useUser } from '@/firebase';
import { collection, doc, query, limit } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { generateMarketInsights, MarketInsightsOutput } from '@/ai/flows/market-insights-flow';
import { MarketTicker, MarketSentiment, FundingRate, OpenInterest, LiquidationCluster } from '@/lib/types';
import { TrendingUp, Brain, ArrowUpRight, ArrowDownRight, Loader2, Zap, BarChart3, ShieldAlert, Activity, DollarSign, Waves } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function MarketIntelligencePage() {
  const { user } = useUser();
  const db = useFirestore();
  const [aiInsights, setAiInsights] = useState<MarketInsightsOutput | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Real-time institutional asset tickers
  const tickersQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'market_tickers'), limit(12));
  }, [db, user]);

  // Global aggregate sentiment
  const sentimentRef = useMemoFirebase(() => {
    if (!db || !user) return null;
    return doc(db, 'market_sentiment', 'current');
  }, [db, user]);

  // Advanced Market Metrics
  const fundingQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'market_funding_rates'), limit(5));
  }, [db, user]);

  const openInterestQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'market_open_interest'), limit(5));
  }, [db, user]);

  const liquidationsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'market_liquidation_clusters'), limit(5));
  }, [db, user]);

  const { data: tickers, isLoading: isTickersLoading } = useCollection<MarketTicker>(tickersQuery);
  const { data: sentiment } = useDoc<MarketSentiment>(sentimentRef);
  const { data: fundingRates } = useCollection<FundingRate>(fundingQuery);
  const { data: openInterest } = useCollection<OpenInterest>(openInterestQuery);
  const { data: liquidations } = useCollection<LiquidationCluster>(liquidationsQuery);

  async function handleGenerateInsights() {
    if (!tickers || !sentiment) return;
    setIsAiLoading(true);
    try {
      const result = await generateMarketInsights({
        tickers: tickers.map(t => ({ asset: t.asset, price: t.price, change24h: t.change24h })),
        sentiment: { score: sentiment.score, label: sentiment.label }
      });
      setAiInsights(result);
    } catch (error) {
      // Errors handled by global listener
    } finally {
      setIsAiLoading(false);
    }
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Intelligence Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to access real-time institutional data streams and AI-augmented trend synthesis.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Market Intelligence</h1>
        <p className="text-muted-foreground text-sm">Real-time institutional data streams and AI-augmented trend synthesis.</p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <SpotlightCard className="col-span-12 lg:col-span-8 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <TrendingUp size={16} />
              Asset Monitoring Core
            </h3>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
              <span className="text-[9px] font-black uppercase text-green">Synced With Exchange Engine</span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isTickersLoading ? (
              Array(6).fill(0).map((_, i) => (
                <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
              ))
            ) : (tickers?.length === 0 ? (
              <div className="col-span-2 py-12 text-center text-[10px] font-black uppercase text-text-muted opacity-50">Synchronizing market depth clusters...</div>
            ) : tickers?.map((ticker) => (
              <div key={ticker.asset} className="flex items-center justify-between p-4 rounded-2xl bg-elevated/30 border border-border-subtle hover:border-primary/50 transition-all group">
                <div>
                  <div className="font-black text-xl tracking-tighter">{ticker.asset}</div>
                  <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest mt-0.5">Vol: ${ticker.volume24h.toLocaleString()}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-mono font-bold tracking-tight">${ticker.price.toLocaleString()}</div>
                  <div className={cn(
                    "text-xs font-black flex items-center justify-end gap-1",
                    ticker.change24h >= 0 ? "text-green" : "text-red"
                  )}>
                    {ticker.change24h >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {ticker.change24h}%
                  </div>
                </div>
              </div>
            )))}
          </div>
        </SpotlightCard>

        <SpotlightCard className="col-span-12 lg:col-span-4 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <BarChart3 size={16} />
                Network Sentiment
              </h3>
            </div>
            <div className="flex flex-col items-center justify-center text-center">
              <div className="relative w-48 h-48 flex items-center justify-center">
                <svg className="w-full h-full rotate-[-90deg]">
                  <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-border-subtle" />
                  <circle 
                    cx="96" 
                    cy="96" 
                    r="80" 
                    stroke="currentColor" 
                    strokeWidth="12" 
                    fill="transparent" 
                    className="text-primary transition-all duration-1000 ease-out" 
                    strokeDasharray="502.6" 
                    strokeDashoffset={502.6 - (502.6 * (sentiment?.score || 50) / 100)} 
                    strokeLinecap="round" 
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-black tracking-tighter">{sentiment?.score || '--'}</span>
                  <span className="text-[10px] font-black uppercase text-primary tracking-widest mt-1">{sentiment?.label || 'Calculating'}</span>
                </div>
              </div>
              <p className="mt-8 text-[11px] text-text-muted leading-relaxed max-w-[260px] font-medium uppercase italic">
                Cross-exchange sentiment aggregation weighting social momentum and volatility regimes.
              </p>
            </div>
          </div>
          
          <Button 
            onClick={handleGenerateInsights} 
            disabled={isAiLoading || !tickers || tickers.length === 0}
            className="w-full mt-10 bg-primary hover:bg-primary/95 text-primary-foreground font-black uppercase text-xs h-14 gap-3 rounded-2xl shadow-[0_0_25px_rgba(96,165,250,0.3)]"
          >
            {isAiLoading ? <Loader2 className="animate-spin" size={18} /> : <Brain size={18} />}
            Generate AI Synthesis Report
          </Button>
        </SpotlightCard>

        <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold uppercase text-text-muted mb-6 flex items-center gap-2">
              <DollarSign size={16} />
              Funding Rates
            </h3>
            <div className="space-y-4">
              {fundingRates?.length === 0 ? (
                <div className="py-4 text-center text-[10px] font-black uppercase text-text-muted opacity-50">Awaiting stream...</div>
              ) : fundingRates?.map((f) => (
                <div key={f.id} className="flex justify-between items-center text-sm">
                  <span className="font-bold">{f.asset}</span>
                  <span className={cn("font-mono font-bold", f.rate >= 0 ? "text-green" : "text-red")}>
                    {(f.rate * 100).toFixed(4)}%
                  </span>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold uppercase text-text-muted mb-6 flex items-center gap-2">
              <Waves size={16} />
              Open Interest
            </h3>
            <div className="space-y-4">
              {openInterest?.length === 0 ? (
                <div className="py-4 text-center text-[10px] font-black uppercase text-text-muted opacity-50">Awaiting stream...</div>
              ) : openInterest?.map((oi) => (
                <div key={oi.id} className="flex justify-between items-center text-sm">
                  <span className="font-bold">{oi.asset}</span>
                  <div className="text-right">
                    <div className="font-mono font-bold">${(oi.value / 1000000).toFixed(1)}M</div>
                    <div className={cn("text-[10px] font-black", oi.change24h >= 0 ? "text-green" : "text-red")}>
                      {oi.change24h >= 0 ? '+' : ''}{oi.change24h}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold uppercase text-text-muted mb-6 flex items-center gap-2">
              <Activity size={16} />
              Liquidation Heat
            </h3>
            <div className="space-y-4">
              {liquidations?.length === 0 ? (
                <div className="py-4 text-center text-[10px] font-black uppercase text-text-muted opacity-50">Awaiting stream...</div>
              ) : liquidations?.map((l) => (
                <div key={l.id} className="flex justify-between items-center text-sm">
                  <div>
                    <span className="font-mono font-bold">${l.priceLevel.toLocaleString()}</span>
                    <Badge variant="outline" className={cn("ml-2 text-[8px] uppercase", l.side === 'long' ? "text-red border-red/20" : "text-green border-green/20")}>
                      {l.side}
                    </Badge>
                  </div>
                  <span className="text-[10px] font-black text-text-muted">${(l.volume / 1000).toFixed(1)}K</span>
                </div>
              ))}
            </div>
          </SpotlightCard>
        </div>

        {aiInsights && (
          <SpotlightCard variant="accent" className="col-span-12 p-8 animate-in fade-in slide-in-from-bottom-6 duration-700 shadow-2xl border-primary/20 bg-primary/5">
            <div className="flex flex-col md:flex-row gap-10">
              <div className="flex-1 space-y-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center text-primary shadow-inner">
                    <Zap size={24} />
                  </div>
                  <h2 className="text-3xl font-black tracking-tighter leading-none">{aiInsights.headline}</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4 border-t border-border-subtle">
                  <div>
                    <h4 className="text-[10px] font-black uppercase tracking-widest text-primary mb-3">Institutional Trends Analysis</h4>
                    <p className="text-xs leading-relaxed text-text-secondary font-medium">{aiInsights.analysis}</p>
                  </div>
                  <div>
                    <h4 className="text-[10px] font-black uppercase tracking-widest text-primary mb-3">Actionable Intelligence Outlook</h4>
                    <p className="text-xs leading-relaxed text-text-secondary font-bold">{aiInsights.recommendation}</p>
                  </div>
                </div>
              </div>
              <div className="w-full md:w-72 space-y-4">
                <div className="p-6 rounded-2xl bg-surface/80 border border-border-subtle backdrop-blur-md">
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-2">Calculated Regime Risk</div>
                  <div className={cn(
                    "text-2xl font-black uppercase tracking-tighter",
                    aiInsights.riskLevel === 'Low' ? "text-green" : 
                    aiInsights.riskLevel === 'Medium' ? "text-amber" : "text-red"
                  )}>
                    {aiInsights.riskLevel} Profile
                  </div>
                </div>
                <div className="p-6 rounded-2xl bg-surface/80 border border-border-subtle backdrop-blur-md">
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-2">Report Timestamp</div>
                  <div className="text-sm font-mono font-bold uppercase">{new Date().toLocaleTimeString()} (UTC)</div>
                </div>
              </div>
            </div>
          </SpotlightCard>
        )}
      </div>
    </div>
  );
}
