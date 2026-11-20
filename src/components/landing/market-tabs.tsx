'use client';

import { useState } from 'react';
import { useMarketData } from '@/providers/market-data-provider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, ShieldCheck, ArrowRight, Activity, Zap } from 'lucide-react';
import Link from 'next/link';

export function MarketTabs() {
  const { tickers } = useMarketData();
  const [activeTab, setActiveTab] = useState('crypto');

  // Multi-asset data categorization
  const cryptoAssets = [
    { symbol: 'BTC/USDT', name: 'Bitcoin', price: 68450.20, change: 3.42, signal: 'STRONG BUY', conf: 91, volume: '24.8B' },
    { symbol: 'ETH/USDT', name: 'Ethereum', price: 3540.80, change: -1.15, signal: 'ACCUMULATE', conf: 78, volume: '12.4B' },
    { symbol: 'SOL/USDT', name: 'Solana', price: 184.60, change: 5.82, signal: 'STRONG BUY', conf: 88, volume: '4.2B' },
    { symbol: 'AVAX/USDT', name: 'Avalanche', price: 28.40, change: 2.15, signal: 'HOLD', conf: 64, volume: '840M' },
  ];

  const forexAssets = [
    { symbol: 'EUR/USD', name: 'Euro / US Dollar', price: 1.0845, change: 0.12, signal: 'MEAN REVERSION', conf: 74, volume: '8.9B' },
    { symbol: 'GBP/USD', name: 'British Pound / US Dollar', price: 1.2710, change: -0.28, signal: 'HOLD', conf: 62, volume: '6.4B' },
    { symbol: 'USD/JPY', name: 'US Dollar / Japanese Yen', price: 156.40, change: 0.45, signal: 'MOMENTUM LONG', conf: 81, volume: '11.2B' },
    { symbol: 'AUD/USD', name: 'Australian Dollar / USD', price: 0.6650, change: -0.18, signal: 'HOLD', conf: 58, volume: '3.1B' },
  ];

  const commoditiesAssets = [
    { symbol: 'XAU/USD', name: 'Spot Gold', price: 2380.50, change: 0.85, signal: 'TREND BREAKOUT', conf: 85, volume: '15.4B' },
    { symbol: 'XAG/USD', name: 'Spot Silver', price: 30.80, change: 1.42, signal: 'STRONG BUY', conf: 82, volume: '4.1B' },
    { symbol: 'WTI/USD', name: 'Crude Oil', price: 79.20, change: -1.65, signal: 'SHORT MOMENTUM', conf: 73, volume: '8.6B' },
    { symbol: 'SPX', name: 'S&P 500 Index', price: 5480.25, change: 0.44, signal: 'ACCUMULATE', conf: 77, volume: '31.2B' },
  ];

  const getActiveList = () => {
    if (activeTab === 'forex') return forexAssets;
    if (activeTab === 'commodities') return commoditiesAssets;
    return cryptoAssets;
  };

  return (
    <section id="markets" className="py-24 border-t border-border/40 bg-surface/30 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary mb-2">
              <Activity size={14} /> Market Intelligence
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-foreground">
              Institutional Asset Feed
            </h2>
            <p className="text-muted-foreground text-sm font-medium mt-2 max-w-xl">
              Live quotes and ML ensemble confidence metrics aggregated from multi-source liquidity pools.
            </p>
          </div>

          {/* Market Tab Switcher */}
          <div className="flex items-center gap-2 p-1.5 rounded-xl border border-border/60 bg-surface/70 backdrop-blur-md">
            <button
              onClick={() => setActiveTab('crypto')}
              className={cn(
                "px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition-all",
                activeTab === 'crypto' ? "bg-primary text-primary-foreground shadow-md" : "text-muted-foreground hover:text-foreground"
              )}
            >
              Crypto
            </button>
            <button
              onClick={() => setActiveTab('forex')}
              className={cn(
                "px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition-all",
                activeTab === 'forex' ? "bg-primary text-primary-foreground shadow-md" : "text-muted-foreground hover:text-foreground"
              )}
            >
              Forex
            </button>
            <button
              onClick={() => setActiveTab('commodities')}
              className={cn(
                "px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition-all",
                activeTab === 'commodities' ? "bg-primary text-primary-foreground shadow-md" : "text-muted-foreground hover:text-foreground"
              )}
            >
              Commodities / Indices
            </button>
          </div>
        </div>

        {/* Asset Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {getActiveList().map((asset, idx) => {
            const isPositive = asset.change >= 0;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl border border-border/60 bg-surface/60 hover:bg-surface/90 hover:border-primary/40 transition-all duration-300 flex flex-col justify-between group shadow-sm hover:shadow-xl"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-black text-muted-foreground">{asset.symbol}</span>
                    <Badge variant="outline" className="text-[9px] font-black tracking-wider uppercase border-border/80 bg-background/50">
                      24h Vol: {asset.volume}
                    </Badge>
                  </div>

                  <h3 className="text-xl font-black text-foreground mt-2 tracking-tight">{asset.name}</h3>
                  <div className="flex items-baseline gap-2.5 mt-3">
                    <span className="text-2xl font-mono font-black text-foreground">
                      ${asset.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                    </span>
                    <span className={cn(
                      "text-xs font-mono font-bold flex items-center",
                      isPositive ? "text-green" : "text-red"
                    )}>
                      {isPositive ? <TrendingUp size={12} className="mr-0.5" /> : <TrendingDown size={12} className="mr-0.5" />}
                      {isPositive ? '+' : ''}{asset.change.toFixed(2)}%
                    </span>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-border/40">
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span className="text-muted-foreground uppercase text-[10px] tracking-wider">Quant Signal</span>
                    <span className="text-primary font-black uppercase tracking-wide">{asset.signal}</span>
                  </div>

                  {/* Confidence Bar */}
                  <div className="mt-2 w-full bg-border/40 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-primary h-full rounded-full transition-all duration-500"
                      style={{ width: `${asset.conf}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-muted-foreground mt-1.5 font-mono">
                    <span>Ensemble Confidence</span>
                    <span className="font-bold text-foreground">{asset.conf}%</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <Link href="/dashboard">
            <Button variant="outline" size="lg" className="uppercase text-xs font-black tracking-wider border-border/80 hover:bg-elevated gap-2">
              Explore All 50+ Tracked Markets in Terminal <ArrowRight size={14} />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
