'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

const fundingRates = [
  { exchange: 'Binance', asset: 'BTCUSDT', rate: 0.0125, nextFunding: '4h 12m' },
  { exchange: 'Bybit', asset: 'ETHUSD', rate: -0.0045, nextFunding: '3h 45m' },
  { exchange: 'OKX', asset: 'SOLUSDT', rate: 0.0089, nextFunding: '2h 30m' },
  { exchange: 'Binance', asset: 'LINKUSDT', rate: 0.0034, nextFunding: '4h 12m' },
];

export function FundingRateMonitor() {
  return (
    <SpotlightCard className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
          <Zap size={16} className="text-amber" />
          Perpetual Funding Rates
        </h3>
      </div>

      <div className="space-y-3">
        {fundingRates.map((item, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-xs font-black text-text-primary">{item.asset}</div>
                  <div className="text-[9px] font-bold text-text-muted uppercase">{item.exchange}</div>
                </div>
              </div>
              <div className={cn(
                "text-sm font-black font-mono",
                item.rate > 0 ? "text-red" : "text-green"
              )}>
                {item.rate > 0 ? '+' : ''}{(item.rate * 100).toFixed(3)}%
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-[10px] font-bold text-text-muted uppercase">Next in {item.nextFunding}</div>
            </div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
