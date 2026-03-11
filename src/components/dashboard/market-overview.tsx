
'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { PriceTicker } from '@/components/shared/price-ticker';
import { useCollection, useFirestore, useMemoFirebase } from '@/firebase';
import { collection, query, limit } from 'firebase/firestore';
import { MarketTicker } from '@/lib/types';
import { Activity, DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

export function MarketOverview() {
  const db = useFirestore();
  const tickersQuery = useMemoFirebase(() => {
    if (!db) return null;
    return query(collection(db, 'marketTickers'), limit(3));
  }, [db]);

  const { data: tickers, isLoading } = useCollection<MarketTicker>(tickersQuery);

  return (
    <SpotlightCard className="p-8 h-full flex flex-col justify-between">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <Activity size={16} className="text-primary" />
          Institutional Depth Core
        </h3>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
             <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
             <span className="text-[9px] font-black uppercase text-green">Synced</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {isLoading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-4 w-20" />
            </div>
          ))
        ) : tickers?.map((ticker) => (
          <div key={ticker.id} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle group hover:border-primary/50 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black text-xs tracking-tighter text-text-secondary uppercase">{ticker.asset}</span>
              <div className={cn(
                "text-[10px] font-black flex items-center gap-0.5",
                ticker.change24h >= 0 ? "text-green" : "text-red"
              )}>
                {ticker.change24h >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                {ticker.change24h}%
              </div>
            </div>
            <PriceTicker initialPrice={ticker.price} className="text-xl" />
            <div className="mt-2 text-[9px] font-black text-text-muted uppercase tracking-widest">
              VOL: ${(ticker.volume24h / 1000000).toFixed(1)}M
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 pt-8 border-t border-border-subtle grid grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <div className="text-[9px] font-black uppercase text-text-muted mb-1">Funding (BTC)</div>
          <div className="text-xs font-mono font-bold text-green">0.0100%</div>
        </div>
        <div>
          <div className="text-[9px] font-black uppercase text-text-muted mb-1">Open Interest</div>
          <div className="text-xs font-mono font-bold text-text-primary">$12.4B</div>
        </div>
        <div>
          <div className="text-[9px] font-black uppercase text-text-muted mb-1">Volatility Index</div>
          <div className="text-xs font-mono font-bold text-amber">Medium (14.2)</div>
        </div>
        <div>
          <div className="text-[9px] font-black uppercase text-text-muted mb-1">Network Load</div>
          <div className="text-xs font-mono font-bold text-primary">14.2 ms</div>
        </div>
      </div>
    </SpotlightCard>
  );
}
