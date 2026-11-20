'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BarChart3, Cpu, Network, Zap, Timer, TrendingUp, AlertCircle } from 'lucide-react';
import { TimeframeSelector } from '@/components/analytics/timeframe-selector';
import { PerformanceCharts } from '@/components/analytics/performance-charts';
import { EquityCurve } from '@/components/backtesting/equity-curve';
import { MonitoringStats, ModelPerformance, PerformancePoint } from '@/lib/types';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function AnalyticsPageContent() {
  const { user } = useUser();
  const [timeframe, setTimeframe] = useState('30d');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [monitoring, setMonitoring] = useState<MonitoringStats | null>(null);
  const [modelPerf, setModelPerf] = useState<ModelPerformance[]>([]);
  const [performancePoints, setPerformancePoints] = useState<PerformancePoint[]>([]);

  useEffect(() => {
    const uid = user?.uid || 'mock-user-001';
    Promise.all([
      api.system.getMonitoringStats(),
      api.system.getModelPerformance(),
      api.portfolio.getPerformancePoints(uid),
    ]).then(([mon, model, perf]) => {
      setMonitoring(mon);
      setModelPerf(model);
      setPerformancePoints(perf);
      setIsLoading(false);
    }).catch(err => {
      setError(err.message || 'Failed to load analytics data');
      setIsLoading(false);
    });
  }, [user]);

  const chartData = monitoring ? Object.entries(monitoring.endpoints).map(([path, stats]) => ({
    endpoint: path.split('/').pop() || path,
    calls: stats.total_calls,
    errors: stats.error_calls,
    avgMs: stats.response_times.avg_ms,
    errorRate: stats.error_rate_pct,
  })) : [];

  const winRateTrend = chartData.slice(0, 5).map((d, i) => ({
    week: `W${i + 1}`,
    Calls: d.calls,
  }));

  const profitFactorTrend = chartData.slice(0, 5).map((d, i) => ({
    week: `W${i + 1}`,
    profitFactor: d.avgMs > 0 ? Math.round(d.calls / d.avgMs * 100) / 10 : 0,
    drawdown: -d.errorRate,
  }));

  const signalAccuracy = chartData.slice(0, 6).map((d, i) => ({
    hour: `${String(i * 4).padStart(2, '0')}:00`,
    accuracy: d.errorRate > 0 ? Math.round(100 - d.errorRate) : 99,
  }));

  const equityCurveData = performancePoints.length > 0
    ? performancePoints.map(p => ({ date: p.date, equity: p.equity }))
    : [{ date: new Date().toISOString().slice(0, 10), equity: 100000 }];

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

      {error && (
        <div className="p-4 rounded-xl bg-red/10 border border-red/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle size={16} className="text-red shrink-0" />
            <span className="text-xs font-bold text-red">{error}</span>
          </div>
          <button onClick={() => { setError(null); setIsLoading(true); window.location.reload(); }} className="text-[10px] font-black uppercase text-red hover:text-red/80 transition-colors">Retry</button>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {Array(4).fill(0).map((_, i) => (
              <div key={i} className="h-28 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
            ))}
          </div>
          <div className="h-[450px] rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Array(3).fill(0).map((_, i) => (
              <div key={i} className="h-64 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            <SpotlightCard className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20"><Cpu size={20} /></div>
                <div>
                  <div className="text-[10px] font-black uppercase text-text-muted">Total Requests</div>
                  <div className="text-xl font-black uppercase">{monitoring?.system_stats.total_requests?.toLocaleString() || '—'}</div>
                </div>
              </div>
              <div className="text-[9px] text-green font-bold uppercase flex items-center gap-1.5 tracking-widest">
                <div className="w-1 h-1 rounded-full bg-green animate-pulse" /> System Operational
              </div>
            </SpotlightCard>
            
            <SpotlightCard className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent border border-accent/20"><Network size={20} /></div>
                <div>
                  <div className="text-[10px] font-black uppercase text-text-muted">Avg. Latency</div>
                  <div className="text-xl font-black uppercase">{monitoring?.system_stats.avg_response_time_ms?.toFixed(1) || '—'} MS</div>
                </div>
              </div>
              <div className="text-[9px] text-accent font-bold uppercase tracking-widest flex items-center gap-1.5">
                <Timer size={10} /> Response Time
              </div>
            </SpotlightCard>

            <SpotlightCard className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-green/10 flex items-center justify-center text-green border border-green/20"><Zap size={20} /></div>
                <div>
                  <div className="text-[10px] font-black uppercase text-text-muted">Error Rate</div>
                  <div className="text-xl font-black uppercase">{monitoring?.system_stats.error_rate_pct?.toFixed(2) || '0'}%</div>
                </div>
              </div>
              <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest">{monitoring?.system_stats.total_errors || 0} total errors</div>
            </SpotlightCard>

            <SpotlightCard className="p-6 border-primary/20 bg-primary/5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center text-primary"><BarChart3 size={20} /></div>
                <div>
                  <div className="text-[10px] font-black uppercase text-primary/70">Model Accuracy</div>
                  <div className="text-xl font-black uppercase">{modelPerf[0] ? `${(modelPerf[0].accuracy * 100).toFixed(1)}%` : '—'}</div>
                </div>
              </div>
              <div className="text-[9px] text-primary font-bold uppercase tracking-widest">{modelPerf[0]?.modelName || 'Signal Model'}</div>
            </SpotlightCard>
          </div>

          <EquityCurve data={equityCurveData} title="Aggregated Network Equity Curve" height={450} />
          
          <div className="flex items-center gap-2 px-2">
            <TrendingUp size={16} className="text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-text-muted">Endpoint Performance</h3>
          </div>

          <PerformanceCharts 
            winRateData={winRateTrend} 
            profitFactorData={profitFactorTrend} 
            accuracyData={signalAccuracy} 
          />
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ErrorBoundary>
      <AnalyticsPageContent />
    </ErrorBoundary>
  );
}
