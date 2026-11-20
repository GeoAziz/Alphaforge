'use client';

import Link from 'next/link';
import { ArrowRight, ChevronRight, Layers } from 'lucide-react';

export function HeroBanner() {
  return (
    <section className="relative pt-12 pb-16 overflow-hidden bg-[#131722] text-[#d1d4dc] font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]">
      {/* TradingView Earth & Blue Atmospheric Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-[#2962ff]/12 blur-[160px] pointer-events-none rounded-full" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[280px] bg-[#089981]/08 blur-[130px] pointer-events-none rounded-full" />

      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 relative z-10 text-center">
        
        {/* Verification Status Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2a2e39] bg-[#1e222d]/90 text-[12px] font-medium text-[#b2b5be] mb-6 hover:border-[#434651] transition-colors shadow-sm">
          <span className="w-2 h-2 rounded-full bg-[#089981] animate-ping" />
          <span className="text-white font-semibold">AlphaForge V3 Platform</span>
          <span className="text-[#787b86]">·</span>
          <span>Where the world tracks quant intelligence</span>
          <ChevronRight size={13} className="text-[#787b86]" />
        </div>

        {/* 
          TradingView Exact Hero Headline 
          Text: "Where the world does markets"
          Font: 80px/96px on desktop, tight letter spacing (-0.03em), solid bright white
        */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[88px] font-extrabold tracking-[-0.035em] leading-[0.98] text-white max-w-5xl mx-auto">
          Where the world <br className="hidden sm:inline" />
          does markets
        </h1>

        {/* TradingView Exact Subtitle */}
        <p className="mt-5 text-base sm:text-lg md:text-[20px] text-[#b2b5be] max-w-2xl mx-auto font-normal leading-relaxed">
          Join 100 million traders and investors taking the future into their own hands.
        </p>

        {/* 
          TradingView Exact CTA: 
          Pill button with "Get started for free" + "$0 forever, no credit card needed"
        */}
        <div className="mt-8 flex flex-col items-center justify-center gap-2.5">
          <Link href="/register">
            <button className="h-12 sm:h-14 px-8 text-sm sm:text-base font-bold bg-[#2962ff] hover:bg-[#1e53e5] text-white rounded-full shadow-lg shadow-[#2962ff]/25 transition-all hover:scale-105 cursor-pointer">
              Get started for free
            </button>
          </Link>
          <div className="text-[13px] text-[#787b86] font-normal">
            $0 forever, no credit card needed
          </div>
        </div>

        {/* Secondary Feature Trigger Button: "Explore all features — For every level of analysis" */}
        <div className="mt-8 flex justify-center">
          <Link href="#supercharts">
            <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full border border-[#2a2e39] bg-[#1e222d]/70 hover:bg-[#2a2e39] transition-all cursor-pointer group">
              <div className="w-6 h-6 rounded-full bg-[#2962ff]/20 text-[#2962ff] flex items-center justify-center">
                <Layers size={13} />
              </div>
              <div className="text-left">
                <span className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1">
                  Explore all features <ChevronRight size={13} className="group-hover:translate-x-0.5 transition-transform" />
                </span>
                <span className="text-[11px] text-[#787b86] block">For every level of quantitative analysis</span>
              </div>
            </div>
          </Link>
        </div>

      </div>
    </section>
  );
}
