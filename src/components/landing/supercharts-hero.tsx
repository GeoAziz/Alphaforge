'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { 
  BarChart2, 
  TrendingUp, 
  TrendingDown, 
  ChevronRight, 
  ArrowUpRight,
  ShieldCheck,
  Maximize2
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function SuperchartsHero() {
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  const [activeIndicator, setActiveIndicator] = useState('EMA + RSI');
  const [chartSymbol, setChartSymbol] = useState('BTCUSDT');

  const symbols = [
    { ticker: 'BTCUSDT', name: 'Bitcoin / TetherUS', price: '68,450.20', change: '+3.42%', isUp: true },
    { ticker: 'SPX', name: 'S&P 500 Index', price: '5,885.20', change: '+0.44%', isUp: true },
    { ticker: 'NVDA', name: 'NVIDIA Corp', price: '142.80', change: '+2.18%', isUp: true },
    { ticker: 'EURUSD', name: 'Euro / US Dollar', price: '1.0845', change: '-0.12%', isUp: false },
    { ticker: 'XAUUSD', name: 'Gold / US Dollar', price: '2,680.50', change: '+0.85%', isUp: true },
  ];

  const timeframes = ['1m', '5m', '15m', '1H', '4H', '1D', '1W', '1M', 'ALL'];

  const indicators = ['EMA + RSI', 'Order Flow Heatmap', 'Volume Profile', 'Ensemble ML Signals'];

  return (
    <section id="supercharts" className="pt-4 pb-14 bg-[#131722] text-[#d1d4dc] font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        
        {/* 
          TradingView Exact Section Heading:
          Stacked Two-Line "Supercharged \n Supercharts"
        */}
        <div className="text-center mb-8">
          <h2 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-[-0.035em] text-white leading-[1.02]">
            <p>Supercharged</p>
            <p>Supercharts</p>
          </h2>
        </div>

        {/* Interactive TradingView Chart Container */}
        <div className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] shadow-2xl overflow-hidden">
          
          {/* Chart Top Toolbar */}
          <div className="flex flex-wrap items-center justify-between border-b border-[#2a2e39] bg-[#171b26] px-4 py-2 gap-3">
            {/* Symbol Switchers */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {symbols.map(s => (
                <button
                  key={s.ticker}
                  onClick={() => setChartSymbol(s.ticker)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 cursor-pointer",
                    chartSymbol === s.ticker
                      ? "bg-[#2962ff] text-white shadow-sm"
                      : "text-[#b2b5be] hover:bg-[#2a2e39] hover:text-white"
                  )}
                >
                  <span>{s.ticker}</span>
                  <span className={cn(
                    "text-[10px] font-mono",
                    chartSymbol === s.ticker ? "text-white/80" : s.isUp ? "text-[#089981]" : "text-[#f23645]"
                  )}>
                    {s.change}
                  </span>
                </button>
              ))}
            </div>

            {/* Timeframes Bar */}
            <div className="flex items-center gap-1 bg-[#131722] p-1 rounded-lg border border-[#2a2e39]">
              {timeframes.map(tf => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  className={cn(
                    "px-2 py-0.5 rounded text-[11px] font-bold font-mono transition-colors cursor-pointer",
                    selectedTimeframe === tf 
                      ? "bg-[#2a2e39] text-white" 
                      : "text-[#787b86] hover:text-[#d1d4dc]"
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>

            {/* Indicators Toggle */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[#787b86] font-medium hidden sm:inline">Overlay:</span>
              <div className="flex items-center gap-1">
                {indicators.slice(0, 2).map(ind => (
                  <button
                    key={ind}
                    onClick={() => setActiveIndicator(ind)}
                    className={cn(
                      "px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border cursor-pointer",
                      activeIndicator === ind
                        ? "border-[#2962ff] bg-[#2962ff]/10 text-[#2962ff]"
                        : "border-[#2a2e39] text-[#787b86] hover:text-[#d1d4dc]"
                    )}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Chart Canvas Area */}
          <div className="relative h-[480px] w-full bg-[#131722] p-5 flex flex-col justify-between overflow-hidden">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 opacity-15 pointer-events-none" style={{
              backgroundImage: 'linear-gradient(to right, #2a2e39 1px, transparent 1px), linear-gradient(to bottom, #2a2e39 1px, transparent 1px)',
              backgroundSize: '40px 40px'
            }} />

            {/* Interactive Live Price Badge */}
            <div className="relative z-10 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#2962ff]/20 border border-[#2962ff]/40 flex items-center justify-center font-bold text-white text-sm">
                  {chartSymbol.slice(0, 3)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-black text-white">{chartSymbol}</span>
                    <span className="text-xs text-[#787b86]">Spot Market</span>
                    <span className="px-2 py-0.5 rounded bg-[#089981]/15 text-[#089981] font-mono text-xs font-bold">
                      ● MARKET OPEN
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 font-mono">
                    <span className="text-2xl font-black text-white">$68,450.20</span>
                    <span className="text-sm font-bold text-[#089981] flex items-center">
                      <TrendingUp size={14} className="mr-0.5" /> +2,260.40 (+3.42%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Live Signal Recommendation Pill */}
              <div className="flex items-center gap-2 p-2 rounded-xl bg-[#1e222d] border border-[#2a2e39]">
                <ShieldCheck size={18} className="text-[#089981]" />
                <div className="text-left">
                  <div className="text-[10px] text-[#787b86] font-bold uppercase">Ensemble Engine Status</div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span className="text-[#089981]">STRONG BUY (Conf 91%)</span>
                    <span className="text-[#787b86]">·</span>
                    <span className="text-[10px] text-[#787b86]">Gate 4: 1.8% Risk</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Vector Simulated Candlestick / Area Chart */}
            <div className="relative z-10 my-auto h-[300px] w-full flex items-center justify-center">
              <svg className="w-full h-full" viewBox="0 0 1000 300" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2962ff" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#2962ff" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Grid guidelines */}
                <line x1="0" y1="75" x2="1000" y2="75" stroke="#2a2e39" strokeDasharray="3 3" opacity="0.6" />
                <line x1="0" y1="150" x2="1000" y2="150" stroke="#2a2e39" strokeDasharray="3 3" opacity="0.6" />
                <line x1="0" y1="225" x2="1000" y2="225" stroke="#2a2e39" strokeDasharray="3 3" opacity="0.6" />

                {/* Primary Price Area */}
                <path
                  d="M0,230 Q120,210 200,180 T400,160 T600,110 T800,70 T1000,45 L1000,300 L0,300 Z"
                  fill="url(#chartGradient)"
                />

                {/* Main Price Line */}
                <path
                  d="M0,230 Q120,210 200,180 T400,160 T600,110 T800,70 T1000,45"
                  fill="none"
                  stroke="#2962ff"
                  strokeWidth="3"
                />

                {/* Secondary EMA 20 Line */}
                <path
                  d="M0,240 Q130,225 220,195 T420,175 T620,130 T820,90 T1000,65"
                  fill="none"
                  stroke="#089981"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                />

                {/* Real-time pulse dot on latest price */}
                <circle cx="1000" cy="45" r="5" fill="#2962ff" className="animate-ping" />
                <circle cx="1000" cy="45" r="4" fill="#ffffff" />
              </svg>
            </div>

            {/* Bottom Bar: Indicators Legend & Time Axis */}
            <div className="relative z-10 flex items-center justify-between border-t border-[#2a2e39]/60 pt-2 text-[11px] text-[#787b86]">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5 text-white font-medium">
                  <span className="w-2.5 h-0.5 bg-[#2962ff]" /> Price Action
                </span>
                <span className="flex items-center gap-1.5 text-[#089981] font-medium">
                  <span className="w-2.5 h-0.5 bg-[#089981]" /> EMA 20 Bull Trend
                </span>
                <span className="flex items-center gap-1.5 text-amber-400 font-medium hidden sm:flex">
                  <span className="w-2.5 h-0.5 bg-amber-400" /> Pre-Trade Gate 4 Protected
                </span>
              </div>
              <div className="font-mono text-[#787b86]">
                UTC 14:38:02 · Realtime WS Data
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
