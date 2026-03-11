
'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

const heatmapData = [
  {
    name: 'BTC',
    size: 45,
    change: 2.4,
    color: 'var(--green)'
  },
  {
    name: 'ETH',
    size: 25,
    change: -1.2,
    color: 'var(--red)'
  },
  {
    name: 'SOL',
    size: 15,
    change: 5.6,
    color: 'var(--green)'
  },
  {
    name: 'LINK',
    size: 8,
    change: 1.1,
    color: 'var(--green)'
  },
  {
    name: 'ARB',
    size: 7,
    change: -3.4,
    color: 'var(--red)'
  }
];

const CustomizedContent = (props: any) => {
  const { root, depth, x, y, width, height, index, name, change } = props;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: change >= 0 ? 'rgba(52, 211, 153, 0.2)' : 'rgba(248, 113, 113, 0.2)',
          stroke: change >= 0 ? 'var(--green)' : 'var(--red)',
          strokeWidth: 1,
          strokeOpacity: 0.5,
        }}
      />
      {width > 40 && height > 40 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 5}
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize={12}
            fontWeight="900"
            className="uppercase tracking-tighter"
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 12}
            textAnchor="middle"
            fill={change >= 0 ? 'var(--green)' : 'var(--red)'}
            fontSize={10}
            fontWeight="700"
          >
            {change >= 0 ? '+' : ''}{change}%
          </text>
        </>
      )}
    </g>
  );
};

export function MarketHeatmap() {
  return (
    <SpotlightCard className="p-8 h-full">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary">Volume Distribution</h3>
        <span className="text-[10px] font-black uppercase text-text-muted">Live Heatmap</span>
      </div>
      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={heatmapData}
            dataKey="size"
            stroke="#fff"
            fill="#8884d8"
            content={<CustomizedContent />}
          >
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}
              itemStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', fontSize: '10px' }}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>
    </SpotlightCard>
  );
}
