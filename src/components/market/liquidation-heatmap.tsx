'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Zap, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

const liquidationClusters = [
  { asset: 'BTC', level: 42500, volume: 145.2, severity: 'high' },
  { asset: 'BTC', level: 39800, volume: 98.5, severity: 'medium' },
  { asset: 'ETH', level: 2250, volume: 542.1, severity: 'high' },
  { asset: 'SOL', level: 95, volume: 234.8, severity: 'low' },
];

export function LiquidationHeatmap() {
  return (
    <SpotlightCard className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
          <AlertTriangle size={16} className="text-red" />
          Liquidation Clusters
        </h3>
      </div>

      <div className="space-y-3">
        {liquidationClusters.map((cluster, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:border-red/30 transition-all group cursor-pointer">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-black text-text-primary">{cluster.asset}</span>
                <div className={cn(
                  "px-2 py-0.5 rounded text-[8px] font-black uppercase",
                  cluster.severity === 'high' ? "bg-red/10 text-red" : cluster.severity === 'medium' ? "bg-amber/10 text-amber" : "bg-green/10 text-green"
                )}>
                  {cluster.severity}
                </div>
              </div>
              <span className="text-[10px] font-bold text-text-muted">${cluster.volume.toFixed(1)}M</span>
            </div>
            <div className="text-xs font-mono text-text-secondary">Price Level: ${cluster.level.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
