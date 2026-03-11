'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, limit, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { MarketplaceStrategy } from '@/lib/types';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ResponsiveContainer,
  LineChart,
  Line,
  Tooltip
} from 'recharts';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { ShieldAlert, TrendingUp, BarChart3, LineChart as LineChartIcon, Target, AlertCircle, Cpu, ShieldCheck, Network, Timer, Zap, PiIcon, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AnalyticsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [timeframe, setTimeframe] = useState('30d');

  // Mock data for charts
  const profitFactorTrend = [
    { week: 'W1', profitFactor: 1.8 },
    { week: 'W2', profitFactor: 2.1 },
    { week: 'W3', profitFactor: 1.9 },
    { week: 'W4', profitFactor: 2.4 },
    { week: 'W5', profitFactor: 2.2 },
  ];

  const winRateTrend = [
    { week: 'W1', Momentum: 65, Reversion: 58, Volatility: 72 },
    { week: 'W2', Momentum: 68, Reversion: 61, Volatility: 75 },
    { week: 'W3', Momentum: 66, Reversion: 59, Volatility: 73 },
    { week: 'W4', Momentum: 71, Reversion: 64, Volatility: 78 },
    { week: 'W5', Momentum: 69, Reversion: 62, Volatility: 76 },
  ];

  const signalAccuracy = [
    { hour: '00:00', accuracy: 82 },
    { hour: '04:00', accuracy: 85 },
    { hour: '08:00', accuracy: 88 },
    { hour: '12:00', accuracy: 84 },
    { hour: '16:00', accuracy: 87 },
    { hour: '20:00', accuracy: 86 },
  ];

  const strategiesQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketplaceStrategies'), orderBy('winRate', 'desc'), limit(5));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<MarketplaceStrategy>(strategiesQuery);

  const strategyData = strategies?.map(s => ({
    name: s.name,
    winRate: s.winRate,
    roi: s.roi
  })) || [];

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <BarChart3 size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Analytics Restricted</h2>
          <p className="text-sm text-text-muted">Sync your institutional node to access system-wide alpha performance metrics and network integrity visualizations.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20 animate-page">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-black tracking-tight uppercase">System Analytics</h1>
          <p className="text-muted-foreground text-sm">Aggregated performance metrics and network-wide signal integrity monitoring.</p>
        </header>

        <div className="flex items-center gap-4">
          <Tabs value={timeframe} onValueChange={setTimeframe} className="w-fit">
            <TabsList className="bg-elevated/50 p-1 rounded-xl h-10">
              <TabsTrigger value="7d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary rounded-lg">7D</TabsTrigger>
              <TabsTrigger value="30d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary rounded-lg">30D</TabsTrigger>
              <TabsTrigger value="90d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary rounded-lg">90D</TabsTrigger>
              <TabsTrigger value="all" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary rounded-lg">All</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
              <Cpu size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Compute Clusters</div>
              <div className="text-xl font-black">12 Active Nodes</div>
            </div>
          </div>
          <div className="text-[10px] text-green font-bold uppercase flex items-center gap-1">
            <ShieldCheck size={10} /> Stability Index: 99.99%
          </div>
        </SpotlightCard>
        
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent border border-accent/20">
              <Network size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Avg. Latency</div>
              <div className="text-xl font-black">14.2 ms</div>
            </div>
          </div>
          <div className="text-[10px] text-accent font-bold uppercase flex items-center gap-1">
            <Timer size={10} /> Ultra-low frequency core
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-green/10 flex items-center justify-center text-green border border-green/20">
              <Zap size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Throughput (24H)</div>
              <div className="text-xl font-black">1.2M Msg</div>
            </div>
          </div>
          <div className="text-[10px] text-text-muted font-bold uppercase">Consensus signals synthesized</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 border-primary/20 bg-primary/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
              <BarChart3 size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-primary/70">Alpha Consensus</div>
              <div className="text-xl font-black">84.2% Accuracy</div>
            </div>
          </div>
          <div className="text-[10px] text-primary font-bold uppercase">High-confidence regime</div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Main Equity Curve with Terminal Glow */}
        <SpotlightCard className="col-span-12 p-8 border-primary/10 relative overflow-hidden">
          <div className="flex items-center justify-between mb-8">
            <div className="space-y-1">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <TrendingUp size={16} className="text-primary" />
                Aggregated Network Equity Curve
              </h3>
              <p className="text-[10px] text-text-muted font-bold uppercase">Combined alpha from all authorized institutional clusters</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded bg-primary" />
                <span className="text-[9px] font-black uppercase text-text-muted">Equity</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded bg-red/40" />
                <span className="text-[9px] font-black uppercase text-text-muted">Drawdown</span>
              </div>
            </div>
          </div>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={signalAccuracy}>
                <defs>
                  <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
                  itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
                />
                <Area type="monotone" dataKey="accuracy" stroke="hsl(var(--primary))" strokeWidth={3} fill="url(#colorEquity)" animationDuration={2000} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          {/* Terminal Glow at right edge */}
          <div className="absolute top-[20%] right-8 w-1 h-[60%] bg-primary shadow-[0_0_30px_rgba(96,165,250,0.8)] animate-pulse rounded-full opacity-50" />
        </SpotlightCard>

        {/* 4 Performance Charts */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-6">
          <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-6">Win Rate Distribution</h3>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={winRateTrend}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 9 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 9 }} />
                <Bar dataKey="Momentum" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SpotlightCard>

        {/* Asset Concentration Pie */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-8">
          <div className="space-y-1 mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <PiIcon size={16} className="text-accent" />
              Asset Concentration
            </h3>
            <p className="text-[10px] text-text-muted font-bold uppercase">Exposure by network asset</p>
          </div>
        </SpotlightCard>

        <SpotlightCard className="col-span-12 lg:col-span-4 p-6">
          <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-6">Asset Concentration</h3>
          <div className="h-[250px] relative">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={profitFactorTrend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="week" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="profitFactor"
                  stroke="var(--green)"
                  strokeWidth={2}
                  dot={{ fill: 'var(--green)', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-xl font-black">AF</span>
              <span className="text-[8px] font-black uppercase text-text-muted">CORE</span>
            </div>
          </div>
        </SpotlightCard>

        {/* Win Rate by Strategy */}
        <SpotlightCard className="col-span-12 lg:col-span-6 p-6">
          <div className="flex items-center gap-2 mb-6">
            <Target size={18} className="text-primary" />
            <h3 className="text-sm font-bold uppercase text-text-muted">Win Rate by Strategy Trend</h3>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={winRateTrend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="week" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line type="monotone" dataKey="Momentum" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Reversion" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Volatility" stroke="var(--green)" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </SpotlightCard>

        {/* Accuracy Over Time */}
        <SpotlightCard className="col-span-12 p-8">
          <div className="flex items-center justify-between mb-8">
            <div className="space-y-1">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <Activity size={16} className="text-green" />
                Network Signal Consensus Accuracy (24H)
              </h3>
              <p className="text-[10px] text-text-muted font-bold uppercase">Stability of algorithmic predictions against tick results</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
              <span className="text-[10px] font-black text-green uppercase">Peak Accuracy: 88.2%</span>
            </div>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={signalAccuracy}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="hour" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="accuracy" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
