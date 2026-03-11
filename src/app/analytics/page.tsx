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
import { Activity, PieChart as PieIcon, BarChart3, ShieldAlert, Cpu, Network, Zap, ShieldCheck, Timer } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

const assetDistribution = [
  { name: 'BTC', value: 45, color: 'hsl(var(--primary))' },
  { name: 'ETH', value: 25, color: '#6366f1' },
  { name: 'SOL', value: 15, color: '#8b5cf6' },
  { name: 'Other', value: 15, color: '#ec4899' },
];

const accuracyHistory = [
  { time: '00:00', accuracy: 82 },
  { time: '04:00', accuracy: 84 },
  { time: '08:00', accuracy: 81 },
  { time: '12:00', accuracy: 88 },
  { time: '16:00', accuracy: 86 },
  { time: '20:00', accuracy: 84 },
  { time: '23:59', accuracy: 85 },
];

export default function AnalyticsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [timeframe, setTimeframe] = useState('30d');

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
    <div className="p-8 space-y-8 pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-black tracking-tight uppercase">System Analytics</h1>
          <p className="text-muted-foreground text-sm">Aggregated performance metrics and network-wide signal integrity monitoring.</p>
        </header>

        <div className="flex items-center gap-4">
          <div className="hidden lg:flex items-center gap-2 text-[9px] font-black uppercase text-green bg-green/10 px-3 py-1 rounded-full border border-green/20">
            <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
            Live Network Feed Active
          </div>
          <Tabs value={timeframe} onValueChange={setTimeframe} className="w-fit">
            <TabsList className="bg-elevated/50 p-1 rounded-xl h-10">
              <TabsTrigger value="7d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">7D</TabsTrigger>
              <TabsTrigger value="30d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">30D</TabsTrigger>
              <TabsTrigger value="90d" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">90D</TabsTrigger>
              <TabsTrigger value="all" className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">All</TabsTrigger>
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
        {/* Alpha Distribution Chart */}
        <SpotlightCard className="col-span-12 lg:col-span-8 p-8 border-primary/10">
          <div className="flex items-center justify-between mb-8">
            <div className="space-y-1">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <BarChart3 size={16} className="text-primary" />
                Strategy Performance Alpha Map
              </h3>
              <p className="text-[10px] text-text-muted font-bold uppercase">Comparing Win Rate vs ROI across top clusters</p>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded bg-primary" />
                <span className="text-[9px] font-black uppercase text-text-muted">Win Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded bg-green" />
                <span className="text-[9px] font-black uppercase text-text-muted">ROI %</span>
              </div>
            </div>
          </div>
          <div className="h-[350px] w-full">
            {isLoading ? (
              <div className="h-full w-full flex items-center justify-center text-[10px] font-black uppercase text-text-muted animate-pulse">Syncing Strategy Cluster Data...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={strategyData}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
                    itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
                  />
                  <Bar dataKey="winRate" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="roi" fill="var(--green)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </SpotlightCard>

        {/* Asset Concentration Pie */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-8">
          <div className="space-y-1 mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <PieIcon size={16} className="text-accent" />
              Asset Concentration
            </h3>
            <p className="text-[10px] text-text-muted font-bold uppercase">Exposure by network asset</p>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={assetDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {assetDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
                  itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-black leading-none">AF</span>
              <span className="text-[8px] font-black uppercase text-text-muted">Core</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-6">
            {assetDistribution.map((asset) => (
              <div key={asset.name} className="flex items-center gap-2 p-2 rounded-lg bg-elevated/20 border border-border-subtle">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: asset.color }} />
                <span className="text-[10px] font-black uppercase text-text-muted">{asset.name}: {asset.value}%</span>
              </div>
            ))}
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
          <div className="h-[250px] w-full">
             <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={accuracyHistory}>
                  <defs>
                    <linearGradient id="colorAccuracy" x1="0" x2="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--green)" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="var(--green)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                  <YAxis domain={[70, 100]} axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
                    itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
                  />
                  <Area type="monotone" dataKey="accuracy" stroke="var(--green)" fillOpacity={1} fill="url(#colorAccuracy)" strokeWidth={2} />
                </AreaChart>
            </ResponsiveContainer>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
