
'use client';

import { 
  Treemap, 
  ResponsiveContainer, 
  Tooltip 
} from 'recharts';
import { cn } from '@/lib/utils';

interface HeatmapChartProps {
  data: any[];
  height?: number;
  className?: string;
}

const CustomizedContent = (props: any) => {
  const { x, y, width, height, name, change } = props;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: change >= 0 ? 'rgba(52, 211, 153, 0.15)' : 'rgba(248, 113, 113, 0.15)',
          stroke: change >= 0 ? 'var(--green)' : 'var(--red)',
          strokeWidth: 1,
          strokeOpacity: 0.5,
        }}
      />
      {width > 40 && height > 20 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 2}
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize={10}
            fontWeight="900"
            className="uppercase tracking-tighter"
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill={change >= 0 ? 'var(--green)' : 'var(--red)'}
            fontSize={9}
            fontWeight="700"
          >
            {change >= 0 ? '+' : ''}{change}%
          </text>
        </>
      )}
    </g>
  );
};

/**
 * HeatmapChart - Custom treemap renderer for volume and risk distribution.
 */
export function HeatmapChart({ 
  data, 
  height = 300,
  className 
}: HeatmapChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
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
  );
}
