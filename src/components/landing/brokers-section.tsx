'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { 
  ShieldCheck, 
  Star, 
  ExternalLink, 
  Lock, 
  Zap, 
  CheckCircle2,
  ChevronRight
} from 'lucide-react';

export function BrokersSection() {
  // Brokers modeled after TradingView "Trading and brokers"
  const brokers = [
    {
      name: "Binance",
      badge: "Highest Liquidity",
      markets: "Crypto, Futures, Options",
      rating: 4.8,
      reviews: "1.2M",
      features: "Direct API Keys, sub-5ms order routing, zero deposit fees",
      logo: "BNC",
      tagColor: "bg-amber-400/10 text-amber-400 border-amber-400/30",
    },
    {
      name: "Bybit",
      badge: "Derivatives Leader",
      markets: "Perpetuals, USDC Margined",
      rating: 4.7,
      reviews: "480k",
      features: "High-frequency WebSocket feeds, unified margin account support",
      logo: "BYB",
      tagColor: "bg-[#2962ff]/10 text-[#2962ff] border-[#2962ff]/30",
    },
    {
      name: "Interactive Brokers",
      badge: "Institutional Multi-Asset",
      markets: "Stocks, Options, Futures, FX",
      rating: 4.9,
      reviews: "2.5M",
      features: "Direct TWS API bridge, low borrow fees, global multi-currency clearing",
      logo: "IBKR",
      tagColor: "bg-[#089981]/10 text-[#089981] border-[#089981]/30",
    },
    {
      name: "OKX",
      badge: "On-Chain & CeFi",
      markets: "Spot, Web3 DEX, Futures",
      rating: 4.6,
      reviews: "390k",
      features: "Non-custodial wallet integration, high rate limits for algo traders",
      logo: "OKX",
      tagColor: "bg-purple-400/10 text-purple-400 border-purple-400/30",
    },
  ];

  return (
    <section id="brokers" className="py-14 bg-[#131722] border-t border-[#2a2e39] text-[#d1d4dc]">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        
        {/* TradingView Heading with Subtitle */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-[#089981] uppercase tracking-wider mb-1">
              <ShieldCheck size={14} /> Verified Exchange Connections
            </div>
            <Link href="/dashboard" className="group flex items-center gap-2">
              <h2 className="text-2xl sm:text-4xl font-black text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-2">
                Trading and brokers <ChevronRight size={24} className="text-[#787b86] group-hover:translate-x-1 transition-transform" />
              </h2>
            </Link>
            <p className="text-xs sm:text-sm text-[#787b86] mt-1 max-w-xl">
              Execute directly from AlphaForge Supercharts through our supported, non-custodial API integrations with zero withdrawal risk.
            </p>
          </div>

          <Link href="/dashboard" className="text-xs font-semibold text-[#2962ff] hover:underline flex items-center gap-1">
            See all supported exchanges <ExternalLink size={12} />
          </Link>
        </div>

        {/* 4 Broker Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {brokers.map((broker, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-5 flex flex-col justify-between hover:border-[#434651] transition-all group shadow-sm hover:shadow-xl"
            >
              <div>
                {/* Header: Logo, Name & Badge */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#131722] border border-[#2a2e39] flex items-center justify-center font-black text-sm text-white group-hover:border-[#2962ff] transition-colors">
                      {broker.logo}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white group-hover:text-[#2962ff] transition-colors">
                        {broker.name}
                      </h3>
                      <div className="text-[11px] text-[#787b86]">{broker.markets}</div>
                    </div>
                  </div>
                </div>

                <div className="mt-3">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${broker.tagColor}`}>
                    {broker.badge}
                  </span>
                </div>

                {/* Rating & Reviews */}
                <div className="flex items-center gap-2 mt-4 font-mono text-xs">
                  <div className="flex items-center gap-1 text-amber-400 font-bold">
                    <Star size={13} fill="currentColor" /> {broker.rating}
                  </div>
                  <span className="text-[#787b86]">·</span>
                  <span className="text-[#787b86] text-[11px]">{broker.reviews} reviews</span>
                </div>

                {/* Description feature */}
                <p className="text-xs text-[#b2b5be] mt-3 leading-relaxed">
                  {broker.features}
                </p>
              </div>

              {/* Action Button */}
              <div className="pt-4 mt-4 border-t border-[#2a2e39]">
                <Link href="/dashboard">
                  <Button 
                    size="sm" 
                    className="w-full text-xs font-bold bg-[#131722] hover:bg-[#2962ff] text-white border border-[#2a2e39] hover:border-[#2962ff] rounded-lg transition-all"
                  >
                    Connect API Key
                  </Button>
                </Link>
                <div className="text-[10px] text-[#787b86] text-center mt-2 flex items-center justify-center gap-1">
                  <Lock size={10} /> Read & Trade permissions only
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
