
'use client';

import { 
  Bar, 
  BarChart as RechartsBar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { cn } from '@/lib/utils';

interface BarChartProps {
  data: any[];
  dataKey: string;
  categoryKey: string;
  color?: string;
  height?: number;
  className?: string;
}

/**
 * BarChart - Recharts wrapper with AlphaForge institutional styling.
 */
export function BarChart({ 
  data, 
  dataKey, 
  categoryKey, 
  color = "var(--primary)", 
  height = 300,
  className 
}: BarChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBar data={data}>
          <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis 
            dataKey={categoryKey} 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 900 }} 
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
            itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
          />
          <Bar 
            dataKey={dataKey} 
            fill={color} 
            radius={[4, 4, 0, 0]} 
            animationDuration={1500}
          />
        </RechartsBar>
      </ResponsiveContainer>
    </div>
  );
}
