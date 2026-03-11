'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useDoc, useMemoFirebase, useUser } from '@/firebase';
import { collection, doc, query, limit } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { generateMarketInsights, MarketInsightsOutput } from '@/ai/flows/market-insights-flow';
import { MarketTicker, MarketSentiment, FundingRate, OpenInterest, OnChainActivity, LiquidationCluster } from '@/lib/types';
import { TrendingUp, Brain, ArrowUpRight, ArrowDownRight, Loader2, Zap, BarChart3, ShieldAlert, Activity, DollarSign, Waves, Network, Database, Fish } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AnimatedCounter } from '@/components/shared/animated-counter';
import { Progress } from '@/components/ui/progress';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

export default function MarketIntelligencePage() {
  const { user } = useUser();
  const db = useFirestore();
  const [aiInsights, setAiInsights] = useState<MarketInsightsOutput | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Real-time institutional asset tickers
  const tickersQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketTickers'), limit(12));
  }, [db, user]);

  // Global aggregate sentiment
  const sentimentRef = useMemoFirebase(() => {
    if (!db || !user) return null;
    return doc(db, 'marketSentiment', 'latest');
  }, [db, user]);

  const fundingQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'fundingRates'), limit(5));
  }, [db, user]);

  const openInterestQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'openInterests'), limit(5));
  }, [db, user]);

  // New simulated data streams for intelligence
  const onChainQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'onChainActivity'), limit(5));
  }, [db, user]);

  const { data: tickers, isLoading: isTickersLoading } = useCollection<MarketTicker>(tickersQuery);
  const { data: sentiment } = useDoc<MarketSentiment>(sentimentRef);
  const { data: fundingRates } = useCollection<FundingRate>(fundingQuery);
  const { data: openInterest } = useCollection<OpenInterest>(openInterestQuery);
  const { data: onChain } = useCollection<OnChainActivity>(onChainQuery);

  const liquidationData = [
    { name: 'BTC Longs', size: 45, type: 'long' },
    { name: 'ETH Shorts', size: 25, type: 'short' },
    { name: 'SOL Longs', size: 15, type: 'long' },
    { name: 'PEPE Longs', size: 10, type: 'long' },
    { name: 'ARB Shorts', size: 5, type: 'short' },
  ];

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
    <div className="p-8 space-y-8 pb-24">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Market Intelligence</h1>
        <p className="text-muted-foreground text-sm">Real-time institutional data streams and AI-augmented trend synthesis.</p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Core Asset Monitoring */}
        <SpotlightCard className="col-span-12 lg:col-span-8 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <TrendingUp size={16} />
              Trend Dashboard
            </h3>
            <div className="flex items-center gap-2 text-[9px] font-black uppercase text-green">
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
              Engine Synced
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isTickersLoading ? (
              Array(6).fill(0).map((_, i) => (
                <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
              ))
            ) : tickers?.map((ticker) => (
              <div key={ticker.asset} className="flex items-center justify-between p-4 rounded-2xl bg-elevated/30 border border-border-subtle hover:border-primary/50 transition-all group">
                <div className="space-y-1">
                  <div className="font-black text-xl tracking-tighter">{ticker.asset}</div>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-[8px] h-4 uppercase font-black border-border-subtle text-text-muted">Vol High</Badge>
                    <Badge variant="outline" className="text-[8px] h-4 uppercase font-black border-primary/20 text-primary">Bullish Bias</Badge>
                  </div>
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
            ))}
          </div>
        </SpotlightCard>

        {/* Sentiment Analysis Gauge & Breakdown */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6 space-y-8 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase text-text-muted mb-8 flex items-center gap-2">
              <BarChart3 size={16} />
              Sentiment Engine
            </h3>
            <div className="flex flex-col items-center justify-center text-center">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full rotate-[-90deg]">
                  <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="10" fill="transparent" className="text-border-subtle" />
                  <circle 
                    cx="80" 
                    cy="80" 
                    r="70" 
                    stroke="currentColor" 
                    strokeWidth="10" 
                    fill="transparent" 
                    className="text-primary transition-all duration-1000 ease-out" 
                    strokeDasharray="439.8" 
                    strokeDashoffset={439.8 - (439.8 * (sentiment?.score || 50) / 100)} 
                    strokeLinecap="round" 
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-4xl font-black tracking-tighter">{sentiment?.score || '--'}</span>
                  <span className="text-[9px] font-black uppercase text-primary tracking-widest">{sentiment?.label || 'Calibrating'}</span>
                </div>
              </div>
              
              <div className="w-full space-y-4 mt-8">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
                    <span>Social Momentum</span>
                    <span>{sentiment?.factors?.social || 0}%</span>
                  </div>
                  <Progress value={sentiment?.factors?.social || 0} className="h-1 bg-border-subtle" />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
                    <span>Order Book Bias</span>
                    <span>{sentiment?.factors?.orderBook || 0}%</span>
                  </div>
                  <Progress value={sentiment?.factors?.orderBook || 0} className="h-1 bg-border-subtle" />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
                    <span>Vol Regime Status</span>
                    <span className="text-amber">Stable</span>
                  </div>
                  <Progress value={42} className="h-1 bg-border-subtle" />
                </div>
              </div>
            </div>
          </div>
          
          <Button 
            onClick={handleGenerateInsights} 
            disabled={isAiLoading || !tickers}
            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-black uppercase text-xs h-14 gap-3 rounded-2xl shadow-[0_0_25px_rgba(96,165,250,0.3)] mt-6"
          >
            {isAiLoading ? <Loader2 className="animate-spin" size={18} /> : <Brain size={18} />}
            AI Market Synthesis
          </Button>
        </SpotlightCard>

        {/* Liquidation Heatmap */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <Zap size={16} />
              Liquidation Heatmap
            </h3>
            <span className="text-[9px] font-black uppercase text-text-muted">Risk Clusters (24H)</span>
          </div>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={liquidationData}
                dataKey="size"
                aspectRatio={4 / 3}
                stroke="#fff"
                fill="#8884d8"
                content={(props: any) => {
                  const { x, y, width, height, name, type } = props;
                  return (
                    <g>
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={height}
                        style={{
                          fill: type === 'long' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(248, 113, 113, 0.15)',
                          stroke: type === 'long' ? 'var(--green)' : 'var(--red)',
                          strokeWidth: 1,
                        }}
                      />
                      {width > 40 && height > 20 && (
                        <text
                          x={x + width / 2}
                          y={y + height / 2 + 4}
                          textAnchor="middle"
                          fill="currentColor"
                          className="text-[10px] font-black uppercase tracking-tighter"
                        >
                          {name}
                        </text>
                      )}
                    </g>
                  );
                }}
              />
            </ResponsiveContainer>
          </div>
        </SpotlightCard>

        {/* On-Chain Activity Monitor */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <Database size={16} />
              On-Chain Activity Dashboard
            </h3>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse" />
              <span className="text-[9px] font-black uppercase text-amber">Whale Tracking Active</span>
            </div>
          </div>
          <div className="space-y-4">
            {onChain?.length === 0 ? (
              <div className="py-12 text-center text-[10px] font-black uppercase text-text-muted opacity-50">Synchronizing node telemetry...</div>
            ) : onChain?.map((activity) => (
              <div key={activity.id} className="p-3 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    activity.type === 'whale_move' ? "bg-amber/10 text-amber" : 
                    activity.type === 'exchange_flow' ? "bg-primary/10 text-primary" : "bg-green/10 text-green"
                  )}>
                    {activity.type === 'whale_move' ? <Fish size={16} /> : 
                     activity.type === 'exchange_flow' ? <Activity size={16} /> : <Zap size={16} />}
                  </div>
                  <div>
                    <div className="text-xs font-black uppercase tracking-tight">{activity.asset} {activity.type.replace('_', ' ')}</div>
                    <div className="text-[10px] text-text-muted font-bold uppercase">{activity.from} → {activity.to}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-black text-text-primary">${(activity.valueUsd / 1000000).toFixed(1)}M</div>
                  <div className="text-[9px] text-text-muted font-bold uppercase">{activity.amount.toLocaleString()} {activity.asset}</div>
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Global Market Monitors */}
        <div className="col-span-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold uppercase text-text-muted mb-6 flex items-center gap-2">
              <DollarSign size={16} />
              Funding Rate Monitor
            </h3>
            <div className="space-y-4">
              {fundingRates?.map((f) => (
                <div key={f.id} className="flex justify-between items-center text-sm p-2 rounded-lg bg-elevated/10">
                  <span className="font-bold">{f.asset}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-black uppercase text-text-muted">{f.exchange}</span>
                    <span className={cn("font-mono font-bold", f.rate >= 0 ? "text-green" : "text-red")}>
                      {(f.rate * 100).toFixed(4)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold uppercase text-text-muted mb-6 flex items-center gap-2">
              <Waves size={16} />
              Open Interest Tracker
            </h3>
            <div className="space-y-4">
              {openInterest?.map((oi) => (
                <div key={oi.id} className="flex justify-between items-center text-sm p-2 rounded-lg bg-elevated/10">
                  <span className="font-bold">{oi.asset}</span>
                  <div className="text-right">
                    <div className="font-mono font-bold">${(oi.value / 1000000000).toFixed(2)}B</div>
                    <div className={cn("text-[10px] font-black", oi.change24h >= 0 ? "text-green" : "text-red")}>
                      {oi.change24h >= 0 ? '+' : ''}{oi.change24h}% (24H)
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SpotlightCard>
        </div>

        {/* AI Synthesis Report Integration */}
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
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-2">Synthesis Timestamp</div>
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