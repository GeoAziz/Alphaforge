'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  TrendingUp, 
  TrendingDown, 
  ChevronRight, 
  BarChart2, 
  Flame, 
  Globe2, 
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function MarketSummaryDashboard() {
  const [activeCategory, setActiveCategory] = useState('indices');

  // Multi-market categories matching TradingView exact Market Summary
  const indices = [
    { symbol: 'SPX', name: 'S&P 500', price: '5,885.20', change: '+0.44%', isUp: true, logo: 'US' },
    { symbol: 'NDX', name: 'Nasdaq 100', price: '20,450.10', change: '+0.72%', isUp: true, logo: 'US' },
    { symbol: 'NI225', name: 'Nikkei 225', price: '38,640.00', change: '-0.35%', isUp: false, logo: 'JP' },
    { symbol: 'UKX', name: 'FTSE 100', price: '8,420.30', change: '+0.15%', isUp: true, logo: 'UK' },
    { symbol: 'DAX', name: 'DAX 40', price: '19,210.50', change: '+0.28%', isUp: true, logo: 'DE' },
  ];

  const cryptoTotals = [
    { symbol: 'TOTAL', name: 'Crypto Total Market Cap', price: '$2.48T', change: '+2.85%', isUp: true, logo: '∑' },
    { symbol: 'BTC.D', name: 'Bitcoin Dominance', price: '58.4%', change: '+0.42%', isUp: true, logo: '₿' },
    { symbol: 'BTCUSD', name: 'Bitcoin', price: '$68,450.20', change: '+3.42%', isUp: true, logo: '₿' },
    { symbol: 'ETHUSD', name: 'Ethereum', price: '$3,540.80', change: '-1.15%', isUp: false, logo: 'Ξ' },
    { symbol: 'SOLUSD', name: 'Solana', price: '$184.60', change: '+5.82%', isUp: true, logo: '◎' },
  ];

  const futuresCommodities = [
    { symbol: 'DXY', name: 'US Dollar Index', price: '104.25', change: '-0.18%', isUp: false, logo: '$' },
    { symbol: 'CL1!', name: 'Light Crude Oil', price: '$78.40', change: '-1.45%', isUp: false, logo: '🛢' },
    { symbol: 'NG1!', name: 'Natural Gas', price: '$2.84', change: '+2.10%', isUp: true, logo: '🔥' },
    { symbol: 'GC1!', name: 'Gold Futures', price: '$2,680.50', change: '+0.85%', isUp: true, logo: 'Au' },
    { symbol: 'SI1!', name: 'Silver Futures', price: '$31.20', change: '+1.62%', isUp: true, logo: 'Ag' },
  ];

  const bondsYields = [
    { symbol: 'US10Y', name: 'US 10 Year Yield', price: '4.42%', change: '+0.03', isUp: true, logo: '10Y' },
    { symbol: 'US02Y', name: 'US 2 Year Yield', price: '4.28%', change: '-0.01', isUp: false, logo: '2Y' },
    { symbol: 'US30Y', name: 'US 30 Year Yield', price: '4.61%', change: '+0.04', isUp: true, logo: '30Y' },
    { symbol: 'AAPL-B', name: 'Apple Inc 5.35% 2036', price: '101.40', change: '+0.12%', isUp: true, logo: '' },
    { symbol: 'MSFT-B', name: 'Microsoft 5.55% 2036', price: '102.15', change: '+0.08%', isUp: true, logo: '⊞' },
  ];

  return (
    <section id="market-summary" className="py-12 bg-[#131722] border-t border-[#2a2e39] text-[#d1d4dc]">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        
        {/* TradingView Heading with Arrow */}
        <div className="flex items-center justify-between mb-6">
          <Link href="/dashboard" className="group flex items-center gap-2">
            <h2 className="text-2xl sm:text-3xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
              Market summary <ChevronRight size={22} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
            </h2>
          </Link>
          <Link href="/dashboard" className="text-xs font-semibold text-[#2962ff] hover:underline flex items-center gap-1">
            See all markets <ArrowUpRight size={13} />
          </Link>
        </div>

        {/* 4 Multi-Asset Columns Grid Matching TradingView Dashboard Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Column 1: Major Indices */}
          <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-4 flex flex-col justify-between hover:border-[#434651] transition-all">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2e39]">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Globe2 size={14} className="text-[#2962ff]" /> Major Indices
                </span>
                <span className="text-[10px] text-[#787b86]">Global Markets</span>
              </div>

              <div className="mt-3 space-y-2.5">
                {indices.map(item => (
                  <Link
                    key={item.symbol}
                    href={`/dashboard?symbol=${item.symbol}`}
                    className="flex items-center justify-between py-1 px-1.5 rounded-lg hover:bg-[#2a2e39] transition-colors group"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded bg-[#131722] text-[10px] font-bold text-white flex items-center justify-center border border-[#2a2e39]">
                        {item.logo}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors">
                          {item.name}
                        </div>
                        <div className="text-[10px] font-mono text-[#787b86]">{item.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-white">{item.price}</div>
                      <div className={cn(
                        "text-[10px] font-mono font-bold",
                        item.isUp ? "text-[#089981]" : "text-[#f23645]"
                      )}>
                        {item.change}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            <Link href="/dashboard" className="pt-3 mt-2 border-t border-[#2a2e39] text-[11px] font-semibold text-[#2962ff] hover:underline flex items-center justify-between">
              <span>See all major indices</span>
              <ChevronRight size={13} />
            </Link>
          </div>

          {/* Column 2: Crypto Market Cap & Dominance */}
          <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-4 flex flex-col justify-between hover:border-[#434651] transition-all">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2e39]">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Flame size={14} className="text-[#f23645]" /> Crypto Overview
                </span>
                <span className="text-[10px] text-[#089981] font-bold">LIVE WS</span>
              </div>

              <div className="mt-3 space-y-2.5">
                {cryptoTotals.map(item => (
                  <Link
                    key={item.symbol}
                    href={`/dashboard?symbol=${item.symbol}`}
                    className="flex items-center justify-between py-1 px-1.5 rounded-lg hover:bg-[#2a2e39] transition-colors group"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded bg-[#131722] text-[11px] font-bold text-amber-400 flex items-center justify-center border border-[#2a2e39]">
                        {item.logo}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors">
                          {item.name}
                        </div>
                        <div className="text-[10px] font-mono text-[#787b86]">{item.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-white">{item.price}</div>
                      <div className={cn(
                        "text-[10px] font-mono font-bold",
                        item.isUp ? "text-[#089981]" : "text-[#f23645]"
                      )}>
                        {item.change}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            <Link href="/dashboard" className="pt-3 mt-2 border-t border-[#2a2e39] text-[11px] font-semibold text-[#2962ff] hover:underline flex items-center justify-between">
              <span>See all crypto coins</span>
              <ChevronRight size={13} />
            </Link>
          </div>

          {/* Column 3: Futures & Commodities */}
          <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-4 flex flex-col justify-between hover:border-[#434651] transition-all">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2e39]">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Layers size={14} className="text-amber-400" /> Futures & Energy
                </span>
                <span className="text-[10px] text-[#787b86]">CME / NYMEX</span>
              </div>

              <div className="mt-3 space-y-2.5">
                {futuresCommodities.map(item => (
                  <Link
                    key={item.symbol}
                    href={`/dashboard?symbol=${item.symbol}`}
                    className="flex items-center justify-between py-1 px-1.5 rounded-lg hover:bg-[#2a2e39] transition-colors group"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded bg-[#131722] text-[10px] font-bold text-white flex items-center justify-center border border-[#2a2e39]">
                        {item.logo}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors">
                          {item.name}
                        </div>
                        <div className="text-[10px] font-mono text-[#787b86]">{item.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-white">{item.price}</div>
                      <div className={cn(
                        "text-[10px] font-mono font-bold",
                        item.isUp ? "text-[#089981]" : "text-[#f23645]"
                      )}>
                        {item.change}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            <Link href="/dashboard" className="pt-3 mt-2 border-t border-[#2a2e39] text-[11px] font-semibold text-[#2962ff] hover:underline flex items-center justify-between">
              <span>See all commodities</span>
              <ChevronRight size={13} />
            </Link>
          </div>

          {/* Column 4: US Yield Curve & Corporate Bonds */}
          <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-4 flex flex-col justify-between hover:border-[#434651] transition-all">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2e39]">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart2 size={14} className="text-[#089981]" /> Yield Curve & Bonds
                </span>
                <span className="text-[10px] text-[#787b86]">US Treasuries</span>
              </div>

              <div className="mt-3 space-y-2.5">
                {bondsYields.map(item => (
                  <Link
                    key={item.symbol}
                    href={`/dashboard?symbol=${item.symbol}`}
                    className="flex items-center justify-between py-1 px-1.5 rounded-lg hover:bg-[#2a2e39] transition-colors group"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded bg-[#131722] text-[10px] font-bold text-white flex items-center justify-center border border-[#2a2e39]">
                        {item.logo}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors">
                          {item.name}
                        </div>
                        <div className="text-[10px] font-mono text-[#787b86]">{item.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-white">{item.price}</div>
                      <div className={cn(
                        "text-[10px] font-mono font-bold",
                        item.isUp ? "text-[#089981]" : "text-[#f23645]"
                      )}>
                        {item.change}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            <Link href="/dashboard" className="pt-3 mt-2 border-t border-[#2a2e39] text-[11px] font-semibold text-[#2962ff] hover:underline flex items-center justify-between">
              <span>See all yields & bonds</span>
              <ChevronRight size={13} />
            </Link>
          </div>

        </div>

      </div>
    </section>
  );
}
