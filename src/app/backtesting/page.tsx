'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useCollection, useMemoFirebase } from '@/firebase';
// import { collection, query } from 'firebase/firestore';
import { api } from '@/lib/api';
import { BacktestResult, Strategy } from '@/lib/types';
import { FlaskConical, Loader2 } from 'lucide-react';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BacktestForm } from '@/components/backtesting/backtest-form';
import { BacktestResults } from '@/components/backtesting/backtest-results';
import { EquityCurve } from '@/components/backtesting/equity-curve';

export default function BacktestingPage() {
  const { user } = useUser();
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);

  useEffect(() => {
    api.strategies.getUserStrategies(user?.uid || 'mock-user-001').then(setStrategies);
  }, [user]);

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
          <h2 className="text-2xl font-black uppercase tracking-tighter">Simulation Restricted</h2>
          <p className="text-sm text-text-muted">Connect your session to access the institutional strategy backtesting lab.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Backtesting Lab</h1>
        <p className="text-muted-foreground text-sm font-medium">Simulate institutional algorithmic performance against historical tick data.</p>
      </header>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-4">
          <BacktestForm 
            strategies={strategies} 
            onRun={handleRunBacktest} 
            isLoading={isRunning} 
          />
        </div>

        <div className="col-span-12 lg:col-span-8 space-y-6">
          {isRunning ? (
            <div className="h-[600px] flex flex-col items-center justify-center space-y-6 rounded-2xl border border-border-subtle bg-surface/30 backdrop-blur-md">
              <Loader2 className="animate-spin text-primary" size={48} />
              <div className="text-center">
                <h3 className="text-xl font-black uppercase text-primary animate-pulse tracking-widest">Computing Alpha Cluster</h3>
                <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mt-2">Syncing telemetry with historical tick data...</p>
              </div>
            </div>
          ) : results ? (
            <div className="space-y-6">
              <BacktestResults results={results} />
              <EquityCurve data={performanceData} />
            </div>
          ) : (
            <div className="h-[600px] flex flex-col items-center justify-center text-center space-y-6 rounded-3xl border border-dashed border-border-subtle bg-surface/30">
              <FlaskConical size={48} className="text-text-muted opacity-20" />
              <div className="space-y-2 max-w-xs">
                <h3 className="text-xl font-black uppercase tracking-widest text-text-muted">Lab Node Idle</h3>
                <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest leading-relaxed">
                  Configure strategy parameters and execute the lab to visualize performance curves.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
