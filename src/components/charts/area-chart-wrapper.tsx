'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, TooltipProps } from 'recharts';

interface AreaChartWrapperProps {
  data: Array<{ date?: string; time?: string; equity?: number; drawdown?: number; value?: number; [key: string]: any }>;
  dataKey: string;
  xAxisKey?: string;
  color?: string;
  height?: number;
  showGrid?: boolean;
  showDots?: boolean;
  animationDuration?: number;
}

export function AreaChartWrapper({
  data,
  dataKey,
  xAxisKey = 'date',
  color = 'hsl(var(--primary))',
  height = 300,
  showGrid = true,
  showDots = false,
  animationDuration = 800,
}: AreaChartWrapperProps) {
  // Custom tooltip for better styling
  const CustomTooltip = (props: TooltipProps<number, string>) => {
    const { active, payload, label } = props;
    if (active && payload && payload.length) {
      const value = payload[0].value;
      const isDrawdown = dataKey === 'drawdown';
      const isPercent = dataKey === 'profitFactor' || dataKey === 'accuracy';
      
      return (
        <div className="bg-surface border border-border-subtle rounded px-3 py-2 shadow-lg">
          <p className="text-xs text-text-secondary">{label}</p>
          <p className={`text-sm font-semibold ${isDrawdown ? 'text-red-400' : 'text-green-400'}`}>
            {typeof value === 'number' ? (isPercent ? `${value.toFixed(1)}%` : `$${value.toFixed(2)}`) : value}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={data}
        margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
      >
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border)"
            vertical={false}
          />
        )}
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
          stroke="var(--border)"
        />
        <YAxis
          tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
          stroke="var(--border)"
          tickFormatter={(value) => {
            if (dataKey === 'accuracy' || dataKey === 'profitFactor') {
              return `${value.toFixed(0)}%`;
            }
            return `$${(value / 1000).toFixed(0)}K`;
          }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          fill={color}
          fillOpacity={0.2}
          dot={showDots}
          animationDuration={animationDuration}
          isAnimationActive={true}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
