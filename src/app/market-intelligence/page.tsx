'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useCollection, useDoc, useMemoFirebase } from '@/firebase';
// import { collection, doc, query, limit } from 'firebase/firestore';
import { api } from '@/lib/api';
import {
  mockTrendIndicators,
  mockSocialSentimentDetails,
  mockOnChainMetricDetails
} from '@/data/mock-market-data';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { generateMarketInsights, MarketInsightsOutput } from '@/ai/flows/market-insights-flow';
import { 
  MarketTicker, 
  MarketSentiment, 
  FundingRate, 
  OpenInterest, 
  TrendIndicator,
  SocialSentimentDetail,
  OnChainMetricDetail,
  MarketDataQuality
} from '@/lib/types';
import { 
  TrendingUp, Brain, ArrowUpRight, ArrowDownRight, Loader2, Zap, 
  ShieldCheck, Gauge, AlertCircle, DollarSign, Waves, MessageSquare, Database, Network
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";

const LiquidationTreemapContent = (props: any) => {
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
          style={{
            fill: 'currentColor',
            fontSize: '10px',
            fontWeight: 900,
            textTransform: 'uppercase',
            letterSpacing: '-0.02em',
          }}
        >
          {name}
        </text>
      )}
    </g>
  );
};

export default function MarketIntelligencePage() {
  const { user } = useUser();
  const [aiInsights, setAiInsights] = useState<MarketInsightsOutput | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Mock data state (replaces 8 Firestore queries)
  const [tickers, setTickers] = useState<MarketTicker[]>([]);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [fundingRates, setFundingRates] = useState<FundingRate[]>([]);
  const [openInterest, setOpenInterest] = useState<OpenInterest[]>([]);
  const [quality, setQuality] = useState<MarketDataQuality[]>([]);

  // These come from mock data directly (not in api.ts yet)
  const trends: TrendIndicator[] = mockTrendIndicators;
  const social: SocialSentimentDetail[] = mockSocialSentimentDetails;
  const metrics: OnChainMetricDetail[] = mockOnChainMetricDetails;

  useEffect(() => {
    Promise.all([
      api.market.getTickers(),
      api.market.getSentiment(),
      api.market.getFundingRates(),
      api.market.getOpenInterest(),
      api.market.getDataQuality(),
    ]).then(([t, s, f, o, q]) => {
      setTickers(t);
      setSentiment(s);
      setFundingRates(f);
      setOpenInterest(o);
      setQuality(q);
    });
  }, []);

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
      // Errors handled globally
    } finally {
      setIsAiLoading(false);
    }
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Zap size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Handshake Restricted</h2>
          <p className="text-sm text-text-muted leading-relaxed">Establish an institutional node connection to access real-time market intelligence streams.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 animate-page">
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
            <span className="text-[9px] font-bold text-text-muted uppercase">Live Refresh</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {trends?.map((trend) => (
              <div key={trend.asset} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle group hover:border-primary/30 transition-all">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-xl font-black tracking-tighter">{trend.asset}</div>
                    <Badge variant="outline" className={cn(
                      "text-[8px] h-4 uppercase font-black",
                      trend.bias === 'Bullish' ? "border-green/20 text-green" : "border-red/20 text-red"
                    )}>
                      {trend.bias} Bias
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] font-black text-text-muted uppercase mb-1">Strength</div>
                    <div className="text-lg font-mono font-bold text-primary">{trend.strength}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { l: 'MA20', v: trend.ma20 },
                    { l: 'MA50', v: trend.ma50 },
                    { l: 'MA200', v: trend.ma200 }
                  ].map(ma => (
                    <div key={ma.l} className="p-2 rounded-lg bg-surface/50 border border-border-subtle text-center">
                      <div className="text-[8px] font-black text-text-muted uppercase">{ma.l}</div>
                      <div className="text-[9px] lg:text-[10px] font-bold font-mono truncate">${ma.v.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Global Sentiment Gauge */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6 space-y-8">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <Gauge size={16} className="text-primary" />
              Sentiment Gauge
            </h3>
          </div>
          <div className="flex flex-col items-center justify-center text-center">
            <div className="relative w-32 lg:w-40 h-32 lg:h-40 flex items-center justify-center">
              <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="50%" cy="50%" r="40%" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-border-subtle" />
                <circle 
                  cx="50%" 
                  cy="50%" 
                  r="40%" 
                  stroke="currentColor" 
                  strokeWidth="8" 
                  fill="transparent" 
                  className="text-primary transition-all duration-1000 ease-out" 
                  strokeDasharray="251.3" 
                  strokeDashoffset={251.3 - (251.3 * (sentiment?.score || 50) / 100)} 
                  strokeLinecap="round" 
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl lg:text-4xl font-black tracking-tighter">{sentiment?.score || '--'}</span>
                <span className="text-[8px] lg:text-[9px] font-black uppercase text-primary tracking-widest">{sentiment?.label || 'Calibrating'}</span>
              </div>
            </div>
            
            <div className="w-full space-y-4 mt-8">
              <div className="space-y-1.5">
                <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
                  <span>Order Book Delta</span>
                  <span className="text-text-primary">{sentiment?.factors?.orderBook || 0}%</span>
                </div>
                <Progress value={sentiment?.factors?.orderBook || 0} className="h-1 bg-border-subtle" />
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
                  <span>Social Alpha Volume</span>
                  <span className="text-text-primary">{sentiment?.factors?.social || 0}%</span>
                </div>
                <Progress value={sentiment?.factors?.social || 0} className="h-1 bg-border-subtle" />
              </div>
            </div>
          </div>
        </SpotlightCard>

        {/* Node Integrity Monitor */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-4 lg:p-6">
          <div className="flex items-center justify-between mb-6 lg:mb-8">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <Network size={16} className="text-amber" />
              Integrity Monitor
            </h3>
            <Badge variant="outline" className="text-[8px] font-black uppercase border-amber/20 text-amber">Active Scan</Badge>
          </div>
          <div className="space-y-3">
            {quality?.map((q) => (
              <div key={q.source} className="flex items-center justify-between p-3 rounded-xl bg-elevated/10 border border-border-subtle">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center relative",
                    q.status === 'Optimal' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                  )}>
                    {q.status === 'Optimal' ? <ShieldCheck size={16} /> : <AlertCircle size={16} className="animate-pulse" />}
                  </div>
                  <div>
                    <div className="text-xs font-black uppercase tracking-tight">{q.source}</div>
                    <div className="text-[9px] text-text-muted font-bold uppercase">{q.asset}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono font-bold text-text-primary">{q.freshness}ms</div>
                  <div className={cn(
                    "text-[8px] font-black uppercase",
                    q.status === 'Optimal' ? "text-green" : "text-red"
                  )}>{q.status}</div>
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Social Sentiment Detail */}
        <SpotlightCard className="col-span-12 lg:col-span-8 p-4 lg:p-6">
          <div className="flex items-center justify-between mb-6 lg:mb-8">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <MessageSquare size={16} className="text-primary" />
              NLP Sentiment Breakdown
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8">
            {social?.map((s) => (
              <div key={s.asset} className="space-y-4">
                <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                  <div className="text-lg font-black">{s.asset} Cluster</div>
                  <div className="text-lg font-mono font-bold text-primary">{s.score}%</div>
                </div>
                <div className="space-y-2">
                  {s.sources.map((src) => (
                    <div key={src.name} className="flex items-center justify-between text-[10px]">
                      <div className="flex items-center gap-2 font-bold text-text-secondary uppercase">
                        <div className="w-1 h-1 rounded-full bg-primary" />
                        {src.name}
                      </div>
                      <Badge variant="outline" className={cn(
                        "text-[8px] font-black h-4 px-1.5 uppercase",
                        src.sentiment === 'Bullish' ? "text-green border-green/20" : 
                        src.sentiment === 'Bearish' ? "text-red border-red/20" : "text-text-muted border-border-subtle"
                      )}>{src.sentiment}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Liquidation Concentration */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-4 lg:p-6">
          <div className="flex items-center justify-between mb-6 lg:mb-8">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <Zap size={16} className="text-amber" />
              Liquidation Heatmap
            </h3>
          </div>
          <div className="h-[200px] lg:h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={liquidationData}
                dataKey="size"
                aspectRatio={4 / 3}
                stroke="#fff"
                fill="#8884d8"
                content={<LiquidationTreemapContent />}
              />
            </ResponsiveContainer>
          </div>
        </SpotlightCard>

        {/* On-Chain Metrics */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-4 lg:p-6">
          <div className="flex items-center justify-between mb-6 lg:mb-8">
            <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
              <Database size={16} className="text-primary" />
              On-Chain Valuation
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {metrics?.map((m) => (
              <div key={m.name + m.asset} className="p-4 rounded-xl bg-elevated/10 border border-border-subtle flex flex-col justify-between h-28 lg:h-32 group hover:border-primary/20 transition-all">
                <div className="flex justify-between items-start">
                  <div className="text-[9px] lg:text-[10px] font-black text-text-muted uppercase tracking-widest">{m.name}</div>
                  <div className={cn(
                    "text-[10px] font-black flex items-center gap-0.5",
                    m.change24h >= 0 ? "text-green" : "text-red"
                  )}>
                    {m.change24h >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                    {m.change24h}%
                  </div>
                </div>
                <div className="flex items-end justify-between">
                  <div className="text-2xl lg:text-3xl font-black font-mono tracking-tighter">{m.value}</div>
                  <Badge variant="outline" className={cn(
                    "text-[8px] font-black uppercase h-5 px-2",
                    m.status === 'Undervalued' ? "border-green/30 text-green" : 
                    m.status === 'Overvalued' ? "border-red/30 text-red" : "border-border-subtle text-text-muted"
                  )}>{m.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Funding Rates & OI - Mobile Grid / Desktop Table */}
        <div className="col-span-12 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SpotlightCard className="p-0 overflow-hidden border-border-subtle">
            <div className="p-6 border-b border-border-subtle bg-elevated/20 flex justify-between items-center">
              <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
                <DollarSign size={16} className="text-green" />
                Funding Rate Hub
              </h3>
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-elevated/50">
                  <TableRow className="border-border-subtle hover:bg-transparent">
                    <TableHead className="text-[9px] font-black uppercase">Asset</TableHead>
                    <TableHead className="text-[9px] font-black uppercase">Exchange</TableHead>
                    <TableHead className="text-[9px] font-black uppercase text-right">Rate (%)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fundingRates?.map((f) => (
                    <TableRow key={f.id} className="border-border-subtle hover:bg-elevated/20 group">
                      <TableCell className="font-bold text-xs">{f.asset}</TableCell>
                      <TableCell className="text-[9px] font-black text-text-muted uppercase">{f.exchange}</TableCell>
                      <TableCell className={cn(
                        "text-right font-mono font-bold text-xs",
                        Math.abs(f.rate) > 0.0001 ? (f.rate > 0 ? "text-green" : "text-red") : "text-text-primary"
                      )}>
                        {(f.rate * 100).toFixed(4)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-0 overflow-hidden border-border-subtle">
            <div className="p-6 border-b border-border-subtle bg-elevated/20 flex justify-between items-center">
              <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
                <Waves size={16} className="text-primary" />
                Open Interest Node
              </h3>
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-elevated/50">
                  <TableRow className="border-border-subtle hover:bg-transparent">
                    <TableHead className="text-[9px] font-black uppercase">Cluster</TableHead>
                    <TableHead className="text-[9px] font-black uppercase">Value (USD)</TableHead>
                    <TableHead className="text-[9px] font-black uppercase text-right">24H Δ</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {openInterest?.map((oi) => (
                    <TableRow key={oi.id} className="border-border-subtle hover:bg-elevated/20 group">
                      <TableCell className="font-bold text-xs">{oi.asset}</TableCell>
                      <TableCell className="text-[10px] font-mono font-bold">${(oi.value / 1000000000).toFixed(2)}B</TableCell>
                      <TableCell className={cn(
                        "text-right font-black text-[10px]",
                        oi.change24h >= 0 ? "text-green" : "text-red"
                      )}>
                        {oi.change24h >= 0 ? '+' : ''}{oi.change24h}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </SpotlightCard>
        </div>
      </div>
    </div>
  );
}
