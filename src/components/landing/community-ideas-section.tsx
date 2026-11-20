'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  Users, 
  Compass, 
  MessageSquare, 
  ThumbsUp, 
  ChevronRight, 
  ArrowUpRight, 
  TrendingUp, 
  TrendingDown,
  Sparkles,
  Code
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function CommunityIdeasSection() {
  const [activeTab, setActiveTab] = useState('editors');

  // Trade ideas extracted directly from TradingView — Track All Markets.html
  const tradeIdeas = [
    {
      title: "The Anthropic IPO: You're Buying the Future, But at What Price?",
      description: "The biggest tech valuation comes with big questions. Anthropic NASDAQ:ANT is making stock market history. Does Claude's moat justify the aggressive multiple?",
      author: "TradingView Quantitative Research",
      ticker: "ANT",
      market: "NASDAQ",
      time: "4h ago",
      likes: 1240,
      comments: 312,
      isBullish: true,
      tag: "IPO Analysis",
    },
    {
      title: "CRWV Fell 50%, Rose 50% and Lost 20% in Weeks. Here's Its Quantitative Profile",
      description: "CoreWeave NASDAQ:CRWV fell nearly 50% between its Oct high and Nov low after questions arose about its GPU cluster financing, then rebounded sharply.",
      author: "moomoo Quant Desk",
      ticker: "CRWV",
      market: "NASDAQ",
      time: "6h ago",
      likes: 890,
      comments: 184,
      isBullish: false,
      tag: "Volatility Breakout",
    },
    {
      title: "EUR/USD Lost Its Range Since June 2025: Is 1.08 Next?",
      description: "EUR/USD is trading around 1.0845 on the daily timeframe after breaking below the multi-month consolidation range. Order flow exhibits seller absorption.",
      author: "PrimeXBT Macro",
      ticker: "EURUSD",
      market: "FOREX",
      time: "8h ago",
      likes: 670,
      comments: 95,
      isBullish: false,
      tag: "Macro FX",
    },
    {
      title: "Gold Hits a 14-Month Low as Fed Talk Turns to 50bp Rate Hikes",
      description: "Gold fell nearly 3% on Nov 18 to around $2,680. Fed Governor comments point toward liquidity tightening. Key institutional demand zones tested.",
      author: "XBTALGO Systems",
      ticker: "XAUUSD",
      market: "COMMODITIES",
      time: "11h ago",
      likes: 1540,
      comments: 420,
      isBullish: true,
      tag: "Trend Reversal",
    },
  ];

  // Algorithmic Indicators & Pine strategies from TradingView HTML
  const indicatorScripts = [
    {
      title: "RedK DualTF Volume-Accelerated CCI (RedK VA-CCI)",
      description: "A modern institutional take on the Commodity Channel Index. Builds dual-timeframe momentum filters and volume delta acceleration alerts.",
      author: "RedKTrader",
      downloads: "42.8k",
      category: "Oscillators",
      language: "Pine Script® v6",
    },
    {
      title: "Volume Profile Anatomies (D / B / P / Double Zone)",
      description: "Constructs live volume profiles from tick data, locates Point of Control (POC) and value areas, and automatically classifies auction structures.",
      author: "kingshukghosh71",
      downloads: "28.5k",
      category: "Order Flow",
      language: "Pine Script® v6",
    },
    {
      title: "Higher Timeframe Trend Frontier (Zeiierman)",
      description: "Adaptive multi-timeframe algorithm visualizing HTF opening levels, dynamic liquidity pools, and directional order flow absorption.",
      author: "Zeiierman",
      downloads: "36.1k",
      category: "Trend Analysis",
      language: "AlphaForge ML",
    },
    {
      title: "PineTunnel: Real-Time Broker Execution Engine",
      description: "Direct zero-latency execution bridge for automated signal order routing, trailing stops, bracket orders, and OCA groups.",
      author: "Fractalyst",
      downloads: "19.4k",
      category: "Automated Execution",
      language: "Python / C++",
    },
  ];

  return (
    <section id="community-ideas" className="py-14 bg-[#131722] border-t border-[#2a2e39] text-[#d1d4dc]">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        
        {/* Section 1: Community Trade Ideas Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-[#2962ff] uppercase tracking-wider mb-1">
              <Users size={14} /> Global Social Intelligence
            </div>
            <Link href="/community" className="group flex items-center gap-2">
              <h2 className="text-2xl sm:text-4xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-2">
                Community ideas <ChevronRight size={24} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
              </h2>
            </Link>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#1e222d] border border-[#2a2e39]">
            <button
              onClick={() => setActiveTab('editors')}
              className={cn(
                "px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all",
                activeTab === 'editors' ? "bg-[#2962ff] text-white shadow-sm" : "text-[#787b86] hover:text-white"
              )}
            >
              Editors&apos; picks
            </button>
            <button
              onClick={() => setActiveTab('popular')}
              className={cn(
                "px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all",
                activeTab === 'popular' ? "bg-[#2962ff] text-white shadow-sm" : "text-[#787b86] hover:text-white"
              )}
            >
              Popular
            </button>
          </div>
        </div>

        {/* Ideas 4-Card Carousel Grid Matching TradingView */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tradeIdeas.map((idea, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-5 flex flex-col justify-between hover:border-[#434651] transition-all group shadow-sm hover:shadow-xl"
            >
              <div>
                {/* Card Top: Ticker & Direction Badge */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-[#131722] border border-[#2a2e39] font-mono text-xs font-bold text-white">
                      {idea.ticker}
                    </span>
                    <span className="text-[10px] text-[#787b86]">{idea.market}</span>
                  </div>
                  <span className={cn(
                    "text-[10px] font-bold px-2 py-0.5 rounded uppercase flex items-center gap-1",
                    idea.isBullish ? "bg-[#089981]/15 text-[#089981]" : "bg-[#f23645]/15 text-[#f23645]"
                  )}>
                    {idea.isBullish ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                    {idea.isBullish ? 'LONG' : 'SHORT'}
                  </span>
                </div>

                {/* Simulated Chart Thumbnail Banner */}
                <div className="w-full h-32 rounded-xl bg-[#131722] border border-[#2a2e39] mb-4 overflow-hidden relative flex items-center justify-center p-2">
                  <svg className="w-full h-full opacity-70" viewBox="0 0 200 80">
                    <path
                      d={idea.isBullish ? "M0,60 Q50,55 100,40 T150,30 T200,10" : "M0,20 Q50,25 100,45 T150,60 T200,75"}
                      fill="none"
                      stroke={idea.isBullish ? "#089981" : "#f23645"}
                      strokeWidth="2.5"
                    />
                    <path
                      d={idea.isBullish ? "M0,60 Q50,55 100,40 T150,30 T200,10 L200,80 L0,80 Z" : "M0,20 Q50,25 100,45 T150,60 T200,75 L200,80 L0,80 Z"}
                      fill={idea.isBullish ? "url(#bullG)" : "url(#bearG)"}
                      opacity="0.3"
                    />
                    <defs>
                      <linearGradient id="bullG" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#089981" />
                        <stop offset="100%" stopColor="#131722" />
                      </linearGradient>
                      <linearGradient id="bearG" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f23645" />
                        <stop offset="100%" stopColor="#131722" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <span className="absolute bottom-2 left-2 text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#1e222d]/80 text-[#b2b5be]">
                    {idea.tag}
                  </span>
                </div>

                {/* Title & Description */}
                <h3 className="text-sm font-bold text-white group-hover:text-[#2962ff] transition-colors line-clamp-2 leading-snug">
                  {idea.title}
                </h3>
                <p className="text-xs text-[#787b86] mt-2 line-clamp-3 leading-relaxed">
                  {idea.description}
                </p>
              </div>

              {/* Author & Metrics Footer */}
              <div className="pt-4 mt-4 border-t border-[#2a2e39] flex items-center justify-between text-xs text-[#787b86]">
                <div className="truncate max-w-[120px] font-medium text-[#b2b5be]">
                  by {idea.author}
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono">
                  <span className="flex items-center gap-1 hover:text-white transition-colors">
                    <ThumbsUp size={12} /> {idea.likes}
                  </span>
                  <span className="flex items-center gap-1 hover:text-white transition-colors">
                    <MessageSquare size={12} /> {idea.comments}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Section 2: Indicators and Strategies Header Matching TradingView */}
        <div id="indicators" className="mt-16 pt-12 border-t border-[#2a2e39]">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-[#089981] uppercase tracking-wider mb-1">
                <Code size={14} /> Open-Source Quant Models
              </div>
              <Link href="/strategies" className="group flex items-center gap-2">
                <h2 className="text-2xl sm:text-4xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-2">
                  Indicators and strategies <ChevronRight size={24} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
                </h2>
              </Link>
            </div>
            <Link href="/strategies" className="text-xs font-semibold text-[#2962ff] hover:underline flex items-center gap-1">
              Explore indicator library <ArrowUpRight size={13} />
            </Link>
          </div>

          {/* 4 Algorithmic Scripts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {indicatorScripts.map((script, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-5 flex flex-col justify-between hover:border-[#434651] transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold text-[#089981] px-2 py-0.5 rounded bg-[#089981]/10 uppercase">
                      {script.category}
                    </span>
                    <span className="text-[10px] font-mono text-[#787b86]">{script.downloads} users</span>
                  </div>

                  <h3 className="text-sm font-bold text-white group-hover:text-[#2962ff] transition-colors line-clamp-2 mt-2">
                    {script.title}
                  </h3>
                  <p className="text-xs text-[#787b86] mt-2 line-clamp-3 leading-relaxed">
                    {script.description}
                  </p>
                </div>

                <div className="pt-3 mt-4 border-t border-[#2a2e39] flex items-center justify-between text-xs text-[#787b86]">
                  <span className="text-[#b2b5be]">by {script.author}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#131722] text-[#787b86]">
                    {script.language}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}
