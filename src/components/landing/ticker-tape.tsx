'use client';

import { useMarketData } from '@/providers/market-data-provider';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';

export function TickerTape() {
  const { tickers, isStale, lastUpdated } = useMarketData();

  // Fallback representative assets if tickers array is still loading
  const displayTickers = tickers.length > 0 ? tickers : [
    { id: '1', asset: 'BTC/USDT', price: 68450.20, change24h: 3.42, change24hAbs: 2260, volume24h: 24890000000, high24h: 69100, low24h: 66200 },
    { id: '2', asset: 'ETH/USDT', price: 3540.80, change24h: -1.15, change24hAbs: -41.2, volume24h: 12450000000, high24h: 3600, low24h: 3490 },
    { id: '3', asset: 'SOL/USDT', price: 184.60, change24h: 5.82, change24hAbs: 10.15, volume24h: 4210000000, high24h: 189, low24h: 172 },
    { id: '4', asset: 'EUR/USD', price: 1.0845, change24h: 0.12, change24hAbs: 0.0013, volume24h: 8900000000, high24h: 1.086, low24h: 1.082 },
    { id: '5', asset: 'XAU/USD', price: 2380.50, change24h: 0.85, change24hAbs: 20.1, volume24h: 15400000000, high24h: 2390, low24h: 2365 },
    { id: '6', asset: 'SPX', price: 5480.25, change24h: 0.44, change24hAbs: 24.1, volume24h: 31200000000, high24h: 5495, low24h: 5450 },
  ];

  return (
    <div className="w-full bg-surface/80 border-b border-border/40 overflow-hidden py-2 backdrop-blur-md relative z-40 select-none">
      <div className="flex items-center gap-2 px-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-1.5 shrink-0 pr-4 border-r border-border/60 text-[10px] font-black uppercase tracking-wider text-muted-foreground">
          <Clock size={12} className={cn(isStale ? "text-amber-400" : "text-primary")} />
          <span>{lastUpdated ? lastUpdated.toLocaleTimeString([], { hour12: false }) : 'LIVE FEED'}</span>
        </div>

        {/* Marquee Wrapper */}
        <div className="flex-1 overflow-hidden relative">
          <div className="flex gap-8 animate-marquee whitespace-nowrap hover:[animation-play-state:paused]">
            {[...displayTickers, ...displayTickers].map((item, idx) => {
              const isPositive = (item.change24h ?? 0) >= 0;
              return (
                <div key={idx} className="inline-flex items-center gap-2.5 text-xs font-mono font-bold tracking-tight">
                  <span className="text-foreground">{item.asset}</span>
                  <span className="text-muted-foreground">
                    ${typeof item.price === 'number' ? item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : item.price}
                  </span>
                  <span className={cn(
                    "inline-flex items-center text-[10px] px-1.5 py-0.5 rounded font-black",
                    isPositive ? "text-green bg-green/10" : "text-red bg-red/10"
                  )}>
                    {isPositive ? <TrendingUp size={10} className="mr-0.5" /> : <TrendingDown size={10} className="mr-0.5" />}
                    {isPositive ? '+' : ''}{(item.change24h ?? 0).toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
