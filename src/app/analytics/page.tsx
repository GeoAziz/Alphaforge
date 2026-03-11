'use client';

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
  Area
} from 'recharts';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Activity, PieChart as PieIcon, BarChart3, ShieldAlert, Cpu, Network } from 'lucide-react';

const assetDistribution = [
  { name: 'BTC', value: 45, color: 'hsl(var(--primary))' },
  { name: 'ETH', value: 25, color: '#6366f1' },
  { name: 'SOL', value: 15, color: '#8b5cf6' },
  { name: 'Other', value: 15, color: '#ec4899' },
];

const volumeHistory = [
  { time: '00:00', volume: 4000 },
  { time: '04:00', volume: 3000 },
  { time: '08:00', volume: 5000 },
  { time: '12:00', volume: 8000 },
  { time: '16:00', volume: 7000 },
  { time: '20:00', volume: 6000 },
  { time: '23:59', volume: 5500 },
];

const assetChartConfig = {
  BTC: { label: "BTC", color: "hsl(var(--primary))" },
  ETH: { label: "ETH", color: "#6366f1" },
  SOL: { label: "SOL", color: "#8b5cf6" },
  Other: { label: "Other", color: "#ec4899" },
} satisfies ChartConfig;

export default function AnalyticsPage() {
  const { user } = useUser();
  const db = useFirestore();

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
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Analytics Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to access system-wide performance metrics and signal integrity analysis.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">System Analytics</h1>
        <p className="text-muted-foreground text-sm">Aggregated performance metrics and network-wide signal integrity.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <Cpu size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Compute Clusters</div>
              <div className="text-xl font-black">12 Active</div>
            </div>
          </div>
          <div className="text-[10px] text-green font-bold uppercase">Node Stability: 99.99%</div>
        </SpotlightCard>
        
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-green/10 flex items-center justify-center text-green">
              <Network size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Network Latency</div>
              <div className="text-xl font-black">14.2 ms</div>
            </div>
          </div>
          <div className="text-[10px] text-green font-bold uppercase">Ultra-low frequency core</div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-amber/10 flex items-center justify-center text-amber">
              <Activity size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Throughput (24H)</div>
              <div className="text-xl font-black">1.2M msgs</div>
            </div>
          </div>
          <div className="text-[10px] text-text-muted font-bold uppercase">Signals synthesized</div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <BarChart3 size={20} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Alpha Consensus</div>
              <div className="text-xl font-black">84.2%</div>
            </div>
          </div>
          <div className="text-[10px] text-primary font-bold uppercase">High-confidence regime</div>
        </SpotlightCard>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Performance by Strategy */}
        <SpotlightCard className="col-span-12 lg:col-span-8 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <BarChart3 size={16} />
              Alpha Distribution by Strategy
            </h3>
          </div>
          <div className="h-[300px] w-full">
            {isLoading ? (
              <div className="h-full w-full flex items-center justify-center text-[10px] font-black uppercase text-text-muted animate-pulse">Syncing Strategy Performance...</div>
            ) : (
              <ChartContainer config={{ 
                winRate: { label: "Win Rate", color: "hsl(var(--primary))" },
                roi: { label: "ROI", color: "var(--green)" }
              }}>
                <BarChart data={strategyData}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="winRate" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="roi" fill="var(--green)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ChartContainer>
            )}
          </div>
        </SpotlightCard>

        {/* Asset Distribution */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6">
          <h3 className="text-sm font-bold uppercase text-text-muted mb-8 flex items-center gap-2">
            <PieIcon size={16} />
            Asset Concentration
          </h3>
          <div className="h-[250px] w-full">
            <ChartContainer config={assetChartConfig}>
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
                <ChartTooltip content={<ChartTooltipContent />} />
              </PieChart>
            </ChartContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {assetDistribution.map((asset) => (
              <div key={asset.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: asset.color }} />
                <span className="text-[10px] font-black uppercase text-text-muted">{asset.name}: {asset.value}%</span>
              </div>
            ))}
          </div>
        </SpotlightCard>

        {/* Volume History */}
        <SpotlightCard className="col-span-12 p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
              <Activity size={16} />
              Network Signal Volume (24H)
            </h3>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
              <span className="text-[10px] font-bold text-green uppercase">Peak Load: 8.2k msg/s</span>
            </div>
          </div>
          <div className="h-[250px] w-full">
             <ChartContainer config={{ 
               volume: { label: "Volume", color: "hsl(var(--primary))" }
             }}>
                <AreaChart data={volumeHistory}>
                  <defs>
                    <linearGradient id="colorVolume" x1="0" x2="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Area type="monotone" dataKey="volume" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorVolume)" strokeWidth={2} />
                </AreaChart>
            </ChartContainer>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
