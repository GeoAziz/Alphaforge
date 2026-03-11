'use client';

import { useState } from 'react';
import { useFirestore, useUser, useCollection, useMemoFirebase } from '@/firebase';
import { collection, query } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BacktestResult, Strategy } from '@/lib/types';
import { Play, FlaskConical, Settings2, Loader2, Calendar, DollarSign, ShieldAlert, Zap, TrendingUp, Activity, BarChart3, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { 
  Area, 
  AreaChart, 
  XAxis, 
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';

export default function BacktestingPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [isRunning, setIsRunning] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [results, setResults] = useState<BacktestResult | null>(null);

  const strategiesQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'strategies'));
  }, [db, user]);

  const { data: strategies } = useCollection<Strategy>(strategiesQuery);

  const performanceData = [
    { date: '2024-01-01', equity: 10000, dd: 0 },
    { date: '2024-01-05', equity: 10250, dd: 0 },
    { date: '2024-01-10', equity: 10100, dd: -1.4 },
    { date: '2024-01-15', equity: 10600, dd: 0 },
    { date: '2024-01-20', equity: 11200, dd: 0 },
    { date: '2024-01-25', equity: 10900, dd: -2.6 },
    { date: '2024-02-01', equity: 11500, dd: 0 },
    { date: '2024-02-05', equity: 12100, dd: 0 },
    { date: '2024-02-10', equity: 11800, dd: -2.4 },
    { date: '2024-02-15', equity: 12400, dd: 0 },
    { date: '2024-02-20', equity: 13200, dd: 0 },
    { date: '2024-02-28', equity: 14500, dd: 0 },
  ];

  function handleRunBacktest() {
    if (!selectedStrategy) return;
    setIsRunning(true);
    setResults(null);
    
    setTimeout(() => {
      setResults({
        id: 'res-' + Math.random().toString(36).substr(2, 9),
        userId: user?.uid || '',
        backtestConfigId: 'config-1',
        winRate: 68.4,
        totalTrades: 142,
        roi: 45.2,
        maxDrawdown: -12.4,
        sharpeRatio: 1.92,
        sortinoRatio: 2.15,
        profitFactor: 2.45,
        equityCurvePointIds: []
      });
      setIsRunning(false);
    }, 2500);
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <FlaskConical size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Simulation Restricted</h2>
          <p className="text-sm text-text-muted">Connect your session to access the institutional strategy backtesting lab.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Backtesting Lab</h1>
        <p className="text-muted-foreground text-sm">Simulate institutional algorithmic performance against historical tick data.</p>
      </header>

      <div className="grid grid-cols-12 gap-8">
        {/* Configuration Panel */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <SpotlightCard className="p-6 space-y-8 border-primary/10">
            <div className="space-y-6">
              <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2">
                <Settings2 size={16} className="text-primary" />
                Parameter Configuration
              </h3>
              
              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase text-text-muted">Algorithm Selection</Label>
                <Select onValueChange={setSelectedStrategy}>
                  <SelectTrigger className="bg-elevated/50 border-border-subtle h-12">
                    <SelectValue placeholder="Select Strategy Cluster" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    {strategies?.map(s => (
                      <SelectItem key={s.id} value={s.id} className="font-bold">{s.name}</SelectItem>
                    ))}
                    <SelectItem value="default" className="font-bold text-text-muted italic">Momentum Alpha Core (Shared)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase text-text-muted">Asset Cluster</Label>
                  <Select defaultValue="BTCUSDT">
                    <SelectTrigger className="bg-elevated/50 border-border-subtle h-12">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="glass">
                      <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                      <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                      <SelectItem value="SOLUSDT">SOL/USDT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase text-text-muted">Resolution</Label>
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
              </div>

              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Label className="text-[10px] font-black uppercase text-text-muted">Initial Capital</Label>
                    <span className="text-xs font-bold text-primary">$10,000</span>
                  </div>
                  <Input type="number" defaultValue={10000} className="bg-elevated/30 border-border-subtle h-12" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Label className="text-[10px] font-black uppercase text-text-muted">Risk Per Trade (%)</Label>
                    <span className="text-xs font-bold text-primary">2.5%</span>
                  </div>
                  <Slider defaultValue={[2.5]} max={10} step={0.1} />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-3">
                <div className="flex items-center gap-2 text-primary">
                  <Calendar size={14} />
                  <span className="text-[10px] font-black uppercase">Historical Window</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-[8px] font-bold text-text-muted uppercase">Start Date</Label>
                    <Input type="date" defaultValue="2024-01-01" className="h-8 bg-surface text-[10px] uppercase font-bold" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[8px] font-bold text-text-muted uppercase">End Date</Label>
                    <Input type="date" defaultValue="2024-03-01" className="h-8 bg-surface text-[10px] uppercase font-bold" />
                  </div>
                </div>
              </div>
            </div>

            <Button 
              onClick={handleRunBacktest}
              disabled={isRunning || !selectedStrategy}
              className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs rounded-2xl shadow-lg"
            >
              {isRunning ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
              Execute Historical Simulation
            </Button>
          </SpotlightCard>
        </div>

        {/* Results Panel */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {isRunning ? (
            <div className="h-[600px] flex flex-col items-center justify-center space-y-6 rounded-2xl border border-border-subtle bg-surface/30 backdrop-blur-md">
              <Loader2 className="animate-spin text-primary" size={48} />
              <div className="text-center">
                <h3 className="text-xl font-black uppercase text-primary animate-pulse">Computing Alpha Cluster</h3>
                <p className="text-[10px] font-bold text-text-muted uppercase">Syncing telemetry with historical tick data...</p>
              </div>
            </div>
          ) : results ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SpotlightCard className="p-6 border-green/20 bg-green/5">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-2 flex items-center gap-1">
                    <TrendingUp size={10} className="text-green" /> ROI
                  </div>
                  <div className="text-3xl font-black text-green">+{results.roi}%</div>
                </SpotlightCard>
                <SpotlightCard className="p-6">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-2">Win Rate</div>
                  <div className="text-3xl font-black">{results.winRate}%</div>
                </SpotlightCard>
                <SpotlightCard className="p-6 border-primary/20 bg-primary/5">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-2">Sharpe Ratio</div>
                  <div className="text-3xl font-black text-primary">{results.sharpeRatio}</div>
                </SpotlightCard>
                <SpotlightCard className="p-6 border-red/20 bg-red/5">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-2">Drawdown</div>
                  <div className="text-3xl font-black text-red">{results.maxDrawdown}%</div>
                </SpotlightCard>
              </div>

              <SpotlightCard className="p-8 border-primary/10 relative overflow-hidden">
                <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2 mb-8">
                  <Activity size={16} className="text-primary" />
                  Equity Curve Simulation
                </h3>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceData}>
                      <defs>
                        <linearGradient id="colorEquityLab" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
                      <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }} />
                      <Area type="monotone" dataKey="equity" stroke="hsl(var(--primary))" strokeWidth={3} fill="url(#colorEquityLab)" animationDuration={2000} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="absolute top-[20%] right-8 w-1 h-[60%] bg-primary shadow-[0_0_30px_rgba(96,165,250,0.8)] animate-pulse rounded-full opacity-50" />
              </SpotlightCard>
            </div>
          ) : (
            <div className="h-[600px] flex flex-col items-center justify-center text-center space-y-6 rounded-2xl border border-dashed border-border-subtle bg-surface/30">
              <FlaskConical size={40} className="text-text-muted" />
              <div className="space-y-2 max-w-xs">
                <h3 className="text-xl font-black uppercase">Simulation Cluster Idle</h3>
                <p className="text-xs text-text-muted">Configure strategy parameters and execute the lab to visualize performance curves.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
