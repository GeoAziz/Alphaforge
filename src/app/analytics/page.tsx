
'use client';

import { useState } from 'react';
import { useUser } from '@/firebase';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BarChart3, Cpu, Network, Zap, Timer, TrendingUp } from 'lucide-react';
import { TimeframeSelector } from '@/components/analytics/timeframe-selector';
import { PerformanceCharts } from '@/components/analytics/performance-charts';
import { EquityCurve } from '@/components/backtesting/equity-curve';

export default function AnalyticsPage() {
  const { user } = useUser();
  const [timeframe, setTimeframe] = useState('30d');

  // Mock data for charts
  const winRateTrend = [
    { week: 'W1', Momentum: 65 },
    { week: 'W2', Momentum: 68 },
    { week: 'W3', Momentum: 66 },
    { week: 'W4', Momentum: 71 },
    { week: 'W5', Momentum: 69 },
  ];

  const profitFactorTrend = [
    { week: 'W1', profitFactor: 1.8, drawdown: -4.2 },
    { week: 'W2', profitFactor: 2.1, drawdown: -2.1 },
    { week: 'W3', profitFactor: 1.9, drawdown: -5.8 },
    { week: 'W4', profitFactor: 2.4, drawdown: -1.5 },
    { week: 'W5', profitFactor: 2.2, drawdown: -3.4 },
  ];

  const signalAccuracy = [
    { hour: '00:00', accuracy: 82 },
    { hour: '04:00', accuracy: 85 },
    { hour: '08:00', accuracy: 88 },
    { hour: '12:00', accuracy: 84 },
    { hour: '16:00', accuracy: 87 },
    { hour: '20:00', accuracy: 86 },
  ];

  const performanceData = [
    { date: '2024-01-01', equity: 100000 },
    { date: '2024-01-15', equity: 106000 },
    { date: '2024-02-01', equity: 115000 },
    { date: '2024-02-15', equity: 124000 },
    { date: '2024-02-28', equity: 145000 },
  ];

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <BarChart3 size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Analytics Restricted</h2>
          <p className="text-sm text-text-muted leading-relaxed uppercase font-bold text-[10px]">Sync institutional node to access system-wide alpha performance metrics.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 animate-page">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-black tracking-tight uppercase leading-none">System Analytics</h1>
          <p className="text-muted-foreground text-sm font-medium">Aggregated performance metrics and network-wide signal integrity monitoring.</p>
        </header>

        <TimeframeSelector value={timeframe} onValueChange={setTimeframe} />
      </div>

      {/* High-Density Stat Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20"><Cpu size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Compute Clusters</div>
              <div className="text-xl font-black uppercase">12 Nodes Live</div>
            </div>
          </div>
          <div className="text-[9px] text-green font-bold uppercase flex items-center gap-1.5 tracking-widest">
            <div className="w-1 h-1 rounded-full bg-green animate-pulse" /> Consensus Optimal
          </div>
        </SpotlightCard>
        
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent border border-accent/20"><Network size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Avg. Latency</div>
              <div className="text-xl font-black uppercase">14.2 MS</div>
            </div>
          </div>
          <div className="text-[9px] text-accent font-bold uppercase tracking-widest flex items-center gap-1.5">
            <Timer size={10} /> Ultra-Low Frequency Core
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-green/10 flex items-center justify-center text-green border border-green/20"><Zap size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Throughput</div>
              <div className="text-xl font-black uppercase">1.2M Msg</div>
            </div>
          </div>
          <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest">24H Consensus Load</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 border-primary/20 bg-primary/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center text-primary"><BarChart3 size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-primary/70">Alpha Accuracy</div>
              <div className="text-xl font-black uppercase">84.2%</div>
            </div>
          </div>
          <div className="text-[9px] text-primary font-bold uppercase tracking-widest">High-Confidence Regime</div>
        </SpotlightCard>
      </div>

      <div className="space-y-8">
        <EquityCurve data={performanceData} title="Aggregated Network Equity Curve" height={450} />
        
        <div className="flex items-center gap-2 px-2">
          <TrendingUp size={16} className="text-primary" />
          <h3 className="text-sm font-black uppercase tracking-widest text-text-muted">Performance Decomposition</h3>
        </div>

        <PerformanceCharts 
          winRateData={winRateTrend} 
          profitFactorData={profitFactorTrend} 
          accuracyData={signalAccuracy} 
        />
      </div>
    </div>
  );
}
