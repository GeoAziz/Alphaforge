'use client';

import { useState } from 'react';
import { useFirestore, useUser, useCollection, useMemoFirebase } from '@/firebase';
import { collection, query, orderBy, limit } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { PerformancePoint, BacktestResult, Strategy } from '@/lib/types';
import { Play, FlaskConical, BarChart3, TrendingUp, ShieldAlert, History, Settings2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { 
  Area, 
  AreaChart, 
  ResponsiveContainer, 
  Tooltip, 
  XAxis, 
  YAxis,
  CartesianGrid
} from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

export default function BacktestingPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [isRunning, setIsRunning] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [results, setResults] = useState<BacktestResult | null>(null);

  const strategiesQuery = useMemoFirebase(() => {
    if (!db) return null;
    return query(collection(db, 'strategies'));
  }, [db]);

  const { data: strategies } = useCollection<Strategy>(strategiesQuery);

  // Mock backtest points for the chart
  const performanceData = [
    { date: '2024-01-01', equity: 10000 },
    { date: '2024-01-05', equity: 10250 },
    { date: '2024-01-10', equity: 10100 },
    { date: '2024-01-15', equity: 10600 },
    { date: '2024-01-20', equity: 11200 },
    { date: '2024-01-25', equity: 10900 },
    { date: '2024-02-01', equity: 11500 },
    { date: '2024-02-05', equity: 12100 },
    { date: '2024-02-10', equity: 11800 },
    { date: '2024-02-15', equity: 12400 },
    { date: '2024-02-20', equity: 13200 },
    { date: '2024-02-28', equity: 14500 },
  ];

  function handleRunBacktest() {
    if (!selectedStrategy) return;
    setIsRunning(true);
    // Simulate backtest processing
    setTimeout(() => {
      setResults({
        id: 'res-' + Math.random().toString(36).substr(2, 9),
        winRate: 68.4,
        totalTrades: 142,
        roi: 45.2,
        maxDrawdown: -12.4,
        sharpeRatio: 1.92,
        sortinoRatio: 2.15,
        profitFactor: 2.45
      });
      setIsRunning(false);
    }, 2000);
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Strategy Backtesting</h1>
        <p className="text-muted-foreground text-sm">Simulate institutional algorithmic performance against historical market data.</p>
      </header>

      <div className="grid grid-cols-12 gap-8">
        {/* Config Panel */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <SpotlightCard className="p-6 space-y-8">
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <Settings2 size={16} />
                Configuration
              </h3>
              
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-text-muted">Algorithm</label>
                <Select onValueChange={setSelectedStrategy}>
                  <SelectTrigger className="bg-elevated/50 border-border-subtle h-12">
                    <SelectValue placeholder="Select Strategy" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    {strategies?.map(s => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-text-muted">Timeframe</label>
                <Select defaultValue="1h">
                  <SelectTrigger className="bg-elevated/50 border-border-subtle h-12">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    <SelectItem value="15m">15 Minutes</SelectItem>
                    <SelectItem value="1h">1 Hour</SelectItem>
                    <SelectItem value="4h">4 Hours</SelectItem>
                    <SelectItem value="1d">1 Day</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-6 py-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-[10px] font-black uppercase text-text-muted">Risk Per Trade</label>
                    <span className="text-xs font-bold text-primary">2.5%</span>
                  </div>
                  <Slider defaultValue={[2.5]} max={10} step={0.5} className="py-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-[10px] font-black uppercase text-text-muted">Initial Balance</label>
                    <span className="text-xs font-bold text-primary">$10,000</span>
                  </div>
                  <Slider defaultValue={[10000]} min={1000} max={100000} step={1000} className="py-2" />
                </div>
              </div>
            </div>

            <Button 
              onClick={handleRunBacktest}
              disabled={isRunning || !selectedStrategy}
              className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-90 transition-all gap-2 shadow-[0_0_20px_rgba(96,165,250,0.3)]"
            >
              {isRunning ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
              Execute Simulation
            </Button>
          </SpotlightCard>
        </div>

        {/* Results Panel */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {results ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SpotlightCard className="p-4">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1">Total ROI</div>
                  <div className="text-2xl font-black text-green">+{results.roi}%</div>
                </SpotlightCard>
                <SpotlightCard className="p-4">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1">Win Rate</div>
                  <div className="text-2xl font-black">{results.winRate}%</div>
                </SpotlightCard>
                <SpotlightCard className="p-4">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1">Sharpe</div>
                  <div className="text-2xl font-black text-primary">{results.sharpeRatio}</div>
                </SpotlightCard>
                <SpotlightCard className="p-4">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1">Max DD</div>
                  <div className="text-2xl font-black text-red">{results.maxDrawdown}%</div>
                </SpotlightCard>
              </div>

              {/* Chart */}
              <SpotlightCard className="p-8 h-[400px]">
                <h3 className="text-sm font-bold uppercase text-text-muted mb-6">Equity Curve (Historical Simulation)</h3>
                <div className="h-full w-full pb-8">
                   <ChartContainer config={{ 
                     equity: { label: "Equity", color: "hsl(var(--primary))" } 
                   }}>
                    <AreaChart data={performanceData}>
                      <defs>
                        <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis 
                        dataKey="date" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                        tickFormatter={(v) => `$${v/1000}k`}
                      />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area 
                        type="monotone" 
                        dataKey="equity" 
                        stroke="hsl(var(--primary))" 
                        strokeWidth={3}
                        fillOpacity={1} 
                        fill="url(#colorEquity)" 
                      />
                    </AreaChart>
                  </ChartContainer>
                </div>
              </SpotlightCard>
            </div>
          ) : (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-center space-y-4 rounded-2xl border border-dashed border-border-subtle bg-surface/30">
              <div className="w-16 h-16 rounded-full bg-elevated/50 flex items-center justify-center text-text-muted">
                <FlaskConical size={32} />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-black uppercase">Simulation Pending</h3>
                <p className="text-sm text-text-muted max-w-xs">Configure your strategy parameters and run the executor to visualize performance curves.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
