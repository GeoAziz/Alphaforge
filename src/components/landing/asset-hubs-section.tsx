'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  TrendingUp, 
  TrendingDown, 
  ChevronRight, 
  ArrowUpRight, 
  BarChart3, 
  Zap, 
  Layers, 
  Sparkles,
  Flame,
  Globe2,
  Calendar,
  ShieldAlert
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function AssetHubsSection() {
  const [stockTab, setStockTab] = useState<'volume' | 'gainers' | 'losers'>('volume');
  const [cryptoTab, setCryptoTab] = useState<'gainers' | 'losers'>('gainers');
  const [forexTimeframe, setForexTimeframe] = useState('1D');

  // US Stocks Active Movers
  const highestVolumeStocks = [
    { ticker: 'NVDA', name: 'NVIDIA Corporation', price: '$142.80', change: '+2.18%', volume: '48.2M', isUp: true },
    { ticker: 'MU', name: 'Micron Technology, Inc.', price: '$104.50', change: '+4.12%', volume: '32.1M', isUp: true },
    { ticker: 'AMD', name: 'Advanced Micro Devices', price: '$138.20', change: '-1.45%', volume: '29.4M', isUp: false },
    { ticker: 'AAPL', name: 'Apple Inc.', price: '$228.60', change: '+0.82%', volume: '28.9M', isUp: true },
    { ticker: 'AMZN', name: 'Amazon.com, Inc.', price: '$204.30', change: '+1.65%', volume: '25.6M', isUp: true },
  ];

  const stockGainers = [
    { ticker: 'AKAN', name: 'Akanda Corp.', price: '$3.42', change: '+42.50%', volume: '18.4M', isUp: true },
    { ticker: 'INHD', name: 'Inno Holdings Inc.', price: '$1.85', change: '+28.40%', volume: '14.2M', isUp: true },
    { ticker: 'CRWD', name: 'CrowdStrike Holdings', price: '$345.20', change: '+11.80%', volume: '9.8M', isUp: true },
    { ticker: 'PANW', name: 'Palo Alto Networks', price: '$382.40', change: '+8.90%', volume: '7.6M', isUp: true },
  ];

  const stockLosers = [
    { ticker: 'CLRO', name: 'ClearOne, Inc.', price: '$0.84', change: '-18.40%', volume: '4.2M', isUp: false },
    { ticker: 'UNH', name: 'UnitedHealth Group', price: '$562.10', change: '-6.80%', volume: '11.5M', isUp: false },
    { ticker: 'BABA', name: 'Alibaba Group', price: '$84.20', change: '-5.12%', volume: '16.8M', isUp: false },
    { ticker: 'TTWO', name: 'Take-Two Interactive', price: '$178.40', change: '-4.25%', volume: '3.9M', isUp: false },
  ];

  // Crypto Movers
  const cryptoGainers = [
    { symbol: 'USD.AI', name: 'Chipi USD.AI', price: '$1.42', change: '+15.64%', isUp: true },
    { symbol: 'LUNC', name: 'Terra Classic', price: '$0.00012', change: '+14.74%', isUp: true },
    { symbol: 'SENT', name: 'Sentient Token', price: '$0.85', change: '+12.86%', isUp: true },
    { symbol: 'ETHFI', name: 'ether.fi', price: '$2.14', change: '+10.35%', isUp: true },
    { symbol: 'GRASS', name: 'Grass Network', price: '$2.88', change: '+9.42%', isUp: true },
  ];

  const cryptoLosers = [
    { symbol: 'SKY', name: 'Sky Protocol', price: '$0.062', change: '-14.82%', isUp: false },
    { symbol: 'O1', name: 'o1.exchange', price: '$4.12', change: '-12.40%', isUp: false },
    { symbol: 'BEAM', name: 'Beam Gaming', price: '$0.018', change: '-9.85%', isUp: false },
    { symbol: '0G', name: '0G Network', price: '$1.12', change: '-8.60%', isUp: false },
  ];

  // Forex Rates Heatmap Table
  const forexPairs = [
    { pair: 'EUR/USD', rate: '1.0845', change: '+0.18%', isUp: true, pips: '+19' },
    { pair: 'USD/JPY', rate: '154.20', change: '-0.35%', isUp: false, pips: '-54' },
    { pair: 'GBP/USD', rate: '1.2710', change: '+0.05%', isUp: true, pips: '+6' },
    { pair: 'AUD/USD', rate: '0.6650', change: '-0.03%', isUp: false, pips: '-2' },
    { pair: 'USD/CHF', rate: '0.8840', change: '+0.11%', isUp: true, pips: '+10' },
    { pair: 'USD/CAD', rate: '1.3980', change: '+0.19%', isUp: true, pips: '+26' },
    { pair: 'NZD/USD', rate: '0.5920', change: '+0.64%', isUp: true, pips: '+38' },
  ];

  return (
    <div className="space-y-12 bg-[#131722] text-[#d1d4dc]">
      
      {/* ======================================================== */}
      {/* 1. US STOCKS HUB                                        */}
      {/* ======================================================== */}
      <section id="stocks-hub" className="py-10 border-t border-[#2a2e39]">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6">
            <Link href="/dashboard" className="group flex items-center gap-2">
              <h2 className="text-2xl sm:text-3xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
                US stocks <ChevronRight size={22} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
              </h2>
            </Link>
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#1e222d] border border-[#2a2e39]">
              <button
                onClick={() => setStockTab('volume')}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-bold transition-all",
                  stockTab === 'volume' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
                )}
              >
                Highest Volume
              </button>
              <button
                onClick={() => setStockTab('gainers')}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-bold transition-all",
                  stockTab === 'gainers' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
                )}
              >
                Top Gainers
              </button>
              <button
                onClick={() => setStockTab('losers')}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-bold transition-all",
                  stockTab === 'losers' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
                )}
              >
                Top Losers
              </button>
            </div>
          </div>

          {/* Stocks Table */}
          <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#171b26] border-b border-[#2a2e39] text-[#787b86] uppercase font-mono">
                  <tr>
                    <th className="py-3 px-4">Symbol / Name</th>
                    <th className="py-3 px-4 text-right">Price</th>
                    <th className="py-3 px-4 text-right">24h Change</th>
                    <th className="py-3 px-4 text-right">Volume</th>
                    <th className="py-3 px-4 text-center">Execution Signal</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2a2e39]/60 font-medium">
                  {(stockTab === 'volume' ? highestVolumeStocks : stockTab === 'gainers' ? stockGainers : stockLosers).map((stock, i) => (
                    <tr key={i} className="hover:bg-[#2a2e39]/50 transition-colors">
                      <td className="py-3 px-4 flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-[#131722] flex items-center justify-center font-bold text-white text-[11px] border border-[#2a2e39]">
                          {stock.ticker.slice(0, 2)}
                        </span>
                        <div>
                          <div className="font-bold text-white flex items-center gap-2">
                            {stock.ticker}
                            <span className="text-[10px] text-[#787b86]">NASDAQ</span>
                          </div>
                          <div className="text-[11px] text-[#787b86]">{stock.name}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white">{stock.price}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold">
                        <span className={cn(
                          "px-2 py-0.5 rounded text-[11px]",
                          stock.isUp ? "bg-[#089981]/15 text-[#089981]" : "bg-[#f23645]/15 text-[#f23645]"
                        )}>
                          {stock.change}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-[#b2b5be]">{stock.volume}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded bg-[#2962ff]/10 text-[#2962ff] text-[10px] font-mono font-bold">
                          GATE 4 VERIFIED
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link href={`/dashboard?symbol=${stock.ticker}`}>
                          <button className="text-[11px] font-bold text-[#2962ff] hover:text-white px-2.5 py-1 rounded bg-[#131722] border border-[#2a2e39] hover:bg-[#2962ff] transition-all">
                            Trade
                          </button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 2. CRYPTO COINS & DEFI HUB                               */}
      {/* ======================================================== */}
      <section id="crypto-hub" className="py-10 border-t border-[#2a2e39]">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6">
            <Link href="/dashboard" className="group flex items-center gap-2">
              <h2 className="text-2xl sm:text-3xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
                Crypto <ChevronRight size={22} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
              </h2>
            </Link>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCryptoTab('gainers')}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-bold transition-all",
                  cryptoTab === 'gainers' ? "bg-[#089981] text-white" : "text-[#787b86] hover:text-white"
                )}
              >
                Top Gainers
              </button>
              <button
                onClick={() => setCryptoTab('losers')}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-bold transition-all",
                  cryptoTab === 'losers' ? "bg-[#f23645] text-white" : "text-[#787b86] hover:text-white"
                )}
              >
                Top Losers
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {(cryptoTab === 'gainers' ? cryptoGainers : cryptoLosers).map((coin, i) => (
              <div
                key={i}
                className="rounded-xl border border-[#2a2e39] bg-[#1e222d] p-4 flex flex-col justify-between hover:border-[#434651] transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-white text-sm group-hover:text-[#2962ff] transition-colors">
                      {coin.symbol}
                    </span>
                    <span className={cn(
                      "text-[10px] font-mono font-bold px-1.5 py-0.5 rounded",
                      coin.isUp ? "bg-[#089981]/15 text-[#089981]" : "bg-[#f23645]/15 text-[#f23645]"
                    )}>
                      {coin.change}
                    </span>
                  </div>
                  <div className="text-xs text-[#787b86] mt-0.5 truncate">{coin.name}</div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#2a2e39] flex items-center justify-between font-mono">
                  <span className="text-xs font-bold text-white">{coin.price}</span>
                  <Link href={`/dashboard?symbol=${coin.symbol}`} className="text-[10px] text-[#2962ff] hover:underline">
                    Analyze →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 3. FOREX & CURRENCIES PERFORMANCE                        */}
      {/* ======================================================== */}
      <section id="forex-hub" className="py-10 border-t border-[#2a2e39]">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-6 gap-4">
            <div>
              <Link href="/dashboard" className="group flex items-center gap-2">
                <h2 className="text-2xl sm:text-3xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
                  Forex performance <ChevronRight size={22} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
                </h2>
              </Link>
              <p className="text-xs text-[#787b86] mt-1">Cross-currency strength matrix and pip differential analysis.</p>
            </div>

            <div className="flex items-center gap-1 bg-[#1e222d] p-1 rounded-lg border border-[#2a2e39]">
              {['1D', '1W', '1M', '3M', '6M', 'YTD', 'ALL'].map(tf => (
                <button
                  key={tf}
                  onClick={() => setForexTimeframe(tf)}
                  className={cn(
                    "px-2.5 py-1 rounded text-xs font-bold font-mono transition-colors",
                    forexTimeframe === tf ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            {forexPairs.map((fx, i) => (
              <div
                key={i}
                className="rounded-xl border border-[#2a2e39] bg-[#1e222d] p-3 text-center hover:border-[#434651] transition-all"
              >
                <div className="text-xs font-bold text-white">{fx.pair}</div>
                <div className="text-sm font-mono font-bold text-white mt-1">{fx.rate}</div>
                <div className={cn(
                  "text-[10px] font-mono font-bold mt-1",
                  fx.isUp ? "text-[#089981]" : "text-[#f23645]"
                )}>
                  {fx.change} ({fx.pips})
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 4. MACRO ECONOMY & ECONOMIC CALENDAR                     */}
      {/* ======================================================== */}
      <section id="economy-hub" className="py-10 border-t border-[#2a2e39]">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6">
            <Link href="/dashboard" className="group flex items-center gap-2">
              <h2 className="text-2xl sm:text-3xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
                Economy & Calendar <ChevronRight size={22} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
              </h2>
            </Link>
            <span className="text-xs text-[#787b86]">High-Impact Global Events</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-[#2a2e39] bg-[#1e222d] p-4">
              <div className="flex items-center justify-between text-xs text-[#787b86] pb-2 border-b border-[#2a2e39]">
                <span className="font-bold text-white flex items-center gap-1">
                  <Calendar size={13} className="text-[#2962ff]" /> FOMC Rate Decision
                </span>
                <span className="px-1.5 py-0.5 rounded bg-[#f23645]/20 text-[#f23645] font-bold text-[9px]">HIGH VOL</span>
              </div>
              <div className="mt-3 text-xs text-[#b2b5be]">
                Target Range: <span className="font-mono text-white font-bold">4.50% - 4.75%</span>
              </div>
              <div className="text-[11px] text-[#787b86] mt-1">Impact: Major volatility expected across USD, Gold, and Crypto.</div>
            </div>

            <div className="rounded-xl border border-[#2a2e39] bg-[#1e222d] p-4">
              <div className="flex items-center justify-between text-xs text-[#787b86] pb-2 border-b border-[#2a2e39]">
                <span className="font-bold text-white flex items-center gap-1">
                  <Calendar size={13} className="text-[#089981]" /> US CPI YoY Inflation
                </span>
                <span className="px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-400 font-bold text-[9px]">MED VOL</span>
              </div>
              <div className="mt-3 text-xs text-[#b2b5be]">
                Forecast: <span className="font-mono text-white font-bold">2.6%</span> · Previous: <span className="font-mono text-white font-bold">2.4%</span>
              </div>
              <div className="text-[11px] text-[#787b86] mt-1">Impact: Treasury yield curve steepening and equities rotation.</div>
            </div>

            <div className="rounded-xl border border-[#2a2e39] bg-[#1e222d] p-4">
              <div className="flex items-center justify-between text-xs text-[#787b86] pb-2 border-b border-[#2a2e39]">
                <span className="font-bold text-white flex items-center gap-1">
                  <Calendar size={13} className="text-amber-400" /> Non-Farm Payrolls (NFP)
                </span>
                <span className="px-1.5 py-0.5 rounded bg-[#f23645]/20 text-[#f23645] font-bold text-[9px]">HIGH VOL</span>
              </div>
              <div className="mt-3 text-xs text-[#b2b5be]">
                Forecast: <span className="font-mono text-white font-bold">+180K</span> jobs
              </div>
              <div className="text-[11px] text-[#787b86] mt-1">Pre-trade circuit breakers dynamically tighten 15m prior to release.</div>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
