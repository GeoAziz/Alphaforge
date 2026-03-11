'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

const trendData = [
  { time: '00:00', momentum: 45, strength: 52 },
  { time: '04:00', momentum: 52, strength: 58 },
  { time: '08:00', momentum: 48, strength: 61 },
  { time: '12:00', momentum: 61, strength: 55 },
  { time: '16:00', momentum: 55, strength: 67 },
  { time: '20:00', momentum: 72, strength: 71 },
  { time: '24:00', momentum: 68, strength: 78 },
];

export function TrendDashboard() {
  const currentMomentum = 68;
  const trend = currentMomentum > 50 ? 'bullish' : 'bearish';

  return (
    <SpotlightCard className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
          <TrendingUp size={16} className="text-primary" />
          Institutional Trend Analysis
        </h3>
        <div className={cn(
          "px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest",
          trend === 'bullish' ? "bg-green/10 text-green" : "bg-red/10 text-red"
        )}>
          {trend === 'bullish' ? '↗ Bullish' : '↘ Bearish'}
        </div>
      </div>

      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="var(--text-muted)" style={{ fontSize: '12px' }} />
            <YAxis stroke="var(--text-muted)" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
              labelStyle={{ color: 'var(--text-primary)' }}
            />
            <Line type="monotone" dataKey="momentum" stroke="var(--primary)" name="Momentum" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="strength" stroke="var(--accent)" name="Strength" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-6 border-t border-border-subtle">
        <div>
          <div className="text-[10px] font-black uppercase text-text-muted mb-2">Current Momentum</div>
          <div className="text-2xl font-black text-primary font-mono">{currentMomentum}</div>
        </div>
        <div>
          <div className="text-[10px] font-black uppercase text-text-muted mb-2">Strength Index</div>
          <div className="text-2xl font-black text-accent font-mono">78</div>
        </div>
      </div>
    </SpotlightCard>
  );
}
