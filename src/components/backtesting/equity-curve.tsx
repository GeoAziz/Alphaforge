
'use client';

import { Activity } from 'lucide-react';
import { 
  Area, 
  AreaChart, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer, 
  Tooltip 
} from 'recharts';
import { SpotlightCard } from '@/components/shared/spotlight-card';

interface EquityCurveProps {
  data: any[];
  title?: string;
  height?: number;
}

export function EquityCurve({ data, title = "Equity Curve Simulation", height = 400 }: EquityCurveProps) {
  return (
    <SpotlightCard className="p-8 border-primary/10 relative overflow-hidden">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-bold uppercase text-text-muted flex items-center gap-2 tracking-widest">
          <Activity size={16} className="text-primary" />
          {title}
        </h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded bg-primary" />
            <span className="text-[9px] font-black uppercase text-text-muted">Alpha Flow</span>
          </div>
        </div>
      </div>

      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorEquityLab" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="date" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
              itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
            />
            <Area 
              type="monotone" 
              dataKey="equity" 
              stroke="hsl(var(--primary))" 
              strokeWidth={3} 
              fill="url(#colorEquityLab)" 
              animationDuration={2000} 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Terminal Glow at right edge - signifies live data anchoring */}
      <div className="absolute top-[20%] right-8 w-1 h-[60%] bg-primary shadow-[0_0_30px_rgba(96,165,250,0.8)] animate-pulse rounded-full opacity-50 pointer-events-none" />
    </SpotlightCard>
  );
}
