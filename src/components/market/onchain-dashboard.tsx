'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';

const onchainMetrics = [
  { label: 'Whale Accumulation', value: '+2,450 BTC', trend: 'up', change: '15%' },
  { label: 'Exchange Inflows', value: '1,230 ETH', trend: 'down', change: '-8%' },
  { label: 'Active Addresses', value: '1.2M', trend: 'up', change: '12%' },
  { label: 'Staking Ratio', value: '34.5%', trend: 'up', change: '2%' },
];

export function OnchainDashboard() {
  return (
    <SpotlightCard className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
          <Activity size={16} className="text-primary" />
          On-Chain Intelligence
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {onchainMetrics.map((metric, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <div className="text-[9px] font-black uppercase text-text-muted mb-3 tracking-widest">{metric.label}</div>
            <div className="flex items-baseline justify-between">
              <div className="text-sm font-black font-mono text-text-primary">{metric.value}</div>
              <div className={cn(
                "text-[10px] font-bold flex items-center gap-1",
                metric.trend === 'up' ? "text-green" : "text-red"
              )}>
                {metric.trend === 'up' ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {metric.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-border-subtle">
        <div className="text-[10px] font-bold text-text-muted uppercase mb-3">Top Whale Movement</div>
        <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
          <div className="text-xs font-bold text-primary">Address 0x4d7f...8e2a</div>
          <div className="text-[9px] text-text-muted mt-1">Deposited 450 BTC to Binance 2h ago - potential liquidation risk</div>
        </div>
      </div>
    </SpotlightCard>
  );
}
