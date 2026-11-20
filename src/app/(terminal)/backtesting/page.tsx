'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useCollection, useMemoFirebase } from '@/firebase';
// import { collection, query } from 'firebase/firestore';
import { api } from '@/lib/api';
import { BacktestResult, Strategy } from '@/lib/types';
import { FlaskConical, Loader2, AlertCircle } from 'lucide-react';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BacktestForm } from '@/components/backtesting/backtest-form';
import { BacktestResults } from '@/components/backtesting/backtest-results';
import { EquityCurve } from '@/components/backtesting/equity-curve';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function BacktestingPageContent() {
  const { user } = useUser();
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isStrategiesLoading, setIsStrategiesLoading] = useState(true);
  const [strategiesError, setStrategiesError] = useState<string | null>(null);

  useEffect(() => {
    api.strategies.getUserStrategies(user?.uid || 'mock-user-001').then(data => {
      setStrategies(data);
      setIsStrategiesLoading(false);
    }).catch(err => {
      setStrategiesError(err.message || 'Failed to load strategies');
      setIsStrategiesLoading(false);
    });
  }, [user]);

  const [equityCurve, setEquityCurve] = useState<{ day: number; equity: number; date: string }[]>([]);
  const [isSyntheticData, setIsSyntheticData] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  function parsePct(v: unknown): number {
    if (typeof v === 'number') return v;
    if (typeof v === 'string') return parseFloat(v.replace('%', '')) || 0;
    return 0;
  }

  async function handleRunBacktest(config: { strategyId?: string; risk?: string }) {
    if (!user?.uid) return;
    setIsRunning(true);
    setResults(null);
    setRunError(null);

    const selectedStrategy = strategies.find(s => s.id === config.strategyId);

    try {
      const response = await api.backtest.run(user.uid, {
        name: selectedStrategy?.name || 'Unnamed Strategy',
        symbols: ['BTC'],
        parameters: { risk: config.risk },
      });

      if (response.results.data_source === 'unavailable') {
        setRunError(response.results.error || 'Not enough historical data to run this backtest.');
        return;
      }

      const m = response.results.metrics;
      setResults({
        id: response.backtest_id,
        userId: user.uid,
        backtestConfigId: config.strategyId || '',
        winRate: parsePct(m.win_rate),
        totalTrades: Number(m.total_trades) || 0,
        roi: parsePct(m.total_return),
        maxDrawdown: parsePct(m.max_drawdown),
        sharpeRatio: Number(m.sharpe_ratio) || 0,
        sortinoRatio: Number(m.sharpe_ratio) || 0, // engine doesn't compute Sortino separately yet
        profitFactor: Number(m.profit_factor) || 0,
        equityCurvePointIds: [],
      });
      setEquityCurve(response.results.equity_curve);
      setIsSyntheticData(response.results.data_source === 'synthetic_demo');
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Backtest failed to run');
    } finally {
      setIsRunning(false);
    }
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

      {strategiesError && (
        <div className="p-4 rounded-xl bg-red/10 border border-red/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle size={16} className="text-red shrink-0" />
            <span className="text-xs font-bold text-red">{strategiesError}</span>
          </div>
          <button onClick={() => { setStrategiesError(null); setIsStrategiesLoading(true); api.strategies.getUserStrategies(user?.uid || 'mock-user-001').then(d => { setStrategies(d); setIsStrategiesLoading(false); }).catch(e => { setStrategiesError(e.message || 'Failed to load'); setIsStrategiesLoading(false); }); }} className="text-[10px] font-black uppercase text-red hover:text-red/80 transition-colors">Retry</button>
        </div>
      )}

      {runError && (
        <div className="mb-6 p-4 rounded-xl border border-red/30 bg-red/5 flex items-center gap-3">
          <AlertCircle size={16} className="text-red shrink-0" />
          <span className="text-xs font-bold text-red">{runError}</span>
        </div>
      )}

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-4">
          <BacktestForm 
            strategies={strategies} 
            onRun={handleRunBacktest} 
            isLoading={isRunning || isStrategiesLoading} 
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
              {isSyntheticData && (
                <div className="flex items-center gap-3 p-4 rounded-xl border border-yellow/30 bg-yellow/5">
                  <AlertCircle size={16} className="text-yellow shrink-0" />
                  <span className="text-[10px] font-bold text-yellow uppercase tracking-widest">
                    Synthetic demo simulation — not a real historical-price replay of this strategy. Do not treat these numbers as verified performance.
                  </span>
                </div>
              )}
              <BacktestResults results={results} />
              <EquityCurve data={equityCurve} />
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

export default function BacktestingPage() {
  return (
    <ErrorBoundary>
      <BacktestingPageContent />
    </ErrorBoundary>
  );
}
