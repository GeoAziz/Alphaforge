
'use client';

import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  Tooltip,
  AreaChart,
  Area
} from 'recharts';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Target, TrendingUp, ShieldAlert, Activity } from 'lucide-react';

interface PerformanceChartsProps {
  winRateData: any[];
  profitFactorData: any[];
  accuracyData: any[];
}

export function PerformanceCharts({ winRateData, profitFactorData, accuracyData }: PerformanceChartsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Win Rate by Strategy */}
      <SpotlightCard className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <Target size={18} className="text-primary" />
          <h3 className="text-sm font-black uppercase text-text-muted tracking-widest">Efficiency by Node</h3>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={winRateData}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }} />
              <Bar dataKey="Momentum" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SpotlightCard>

      {/* Profit Factor Trend */}
      <SpotlightCard className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp size={18} className="text-green" />
          <h3 className="text-sm font-black uppercase text-text-muted tracking-widest">Alpha Yield Factor</h3>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={profitFactorData}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }} />
              <Line type="monotone" dataKey="profitFactor" stroke="var(--green)" strokeWidth={3} dot={{ fill: 'var(--green)', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </SpotlightCard>

      {/* Drawdown Node */}
      <SpotlightCard className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <ShieldAlert size={18} className="text-red" />
          <h3 className="text-sm font-black uppercase text-text-muted tracking-widest">Drawdown Integrity</h3>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={profitFactorData}>
              <defs>
                <linearGradient id="colorRed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--red)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--red)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <Area type="monotone" dataKey="drawdown" stroke="var(--red)" fill="url(#colorRed)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </SpotlightCard>

      {/* Network Accuracy */}
      <SpotlightCard className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <Activity size={18} className="text-accent" />
          <h3 className="text-sm font-black uppercase text-text-muted tracking-widest">Node Consensus Accuracy</h3>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={accuracyData}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} />
              <Bar dataKey="accuracy" fill="var(--accent)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SpotlightCard>
    </div>
  );
}
