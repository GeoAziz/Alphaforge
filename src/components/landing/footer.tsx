'use client';

import Link from 'next/link';
import { Terminal, ShieldCheck, Globe, CheckCircle2 } from 'lucide-react';

export function LandingFooter() {
  return (
    <footer className="border-t border-[#2a2e39] bg-[#0c0e15] text-[#b2b5be] py-16 text-xs">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        
        {/* Main Deep Directory Grid (6 Columns Matching TradingView) */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 pb-12 border-b border-[#2a2e39]">
          
          {/* Column 1: Products */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Products</h4>
            <ul className="space-y-2.5">
              <li><Link href="#supercharts" className="hover:text-white transition-colors">Supercharts</Link></li>
              <li><Link href="/dashboard" className="hover:text-white transition-colors">Trading Terminal</Link></li>
              <li><Link href="/signals" className="hover:text-white transition-colors">AI Signals Stream</Link></li>
              <li><Link href="/strategies" className="hover:text-white transition-colors">Pine Script® Library</Link></li>
              <li><Link href="/backtesting" className="hover:text-white transition-colors">Backtesting Engine</Link></li>
              <li><Link href="/market-intelligence" className="hover:text-white transition-colors">Order Flow Heatmaps</Link></li>
            </ul>
          </div>

          {/* Column 2: Markets */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Markets</h4>
            <ul className="space-y-2.5">
              <li><Link href="#stocks-hub" className="hover:text-white transition-colors">US Stocks Screener</Link></li>
              <li><Link href="#crypto-hub" className="hover:text-white transition-colors">Crypto Coins & Futures</Link></li>
              <li><Link href="#forex-hub" className="hover:text-white transition-colors">Forex & Currencies</Link></li>
              <li><Link href="#futures-hub" className="hover:text-white transition-colors">Commodities & Energy</Link></li>
              <li><Link href="#economy-hub" className="hover:text-white transition-colors">Treasury Yield Curves</Link></li>
              <li><Link href="#economy-hub" className="hover:text-white transition-colors">Economic Calendar</Link></li>
            </ul>
          </div>

          {/* Column 3: Community */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Community</h4>
            <ul className="space-y-2.5">
              <li><Link href="#community-ideas" className="hover:text-white transition-colors">Trade Ideas</Link></li>
              <li><Link href="#indicators" className="hover:text-white transition-colors">Indicators & Scripts</Link></li>
              <li><Link href="/community" className="hover:text-white transition-colors">Social Discussions</Link></li>
              <li><Link href="/tournaments" className="hover:text-white transition-colors">Alpha Tournaments</Link></li>
              <li><Link href="/creator/verification" className="hover:text-white transition-colors">Creator Program</Link></li>
              <li><Link href="/marketplace" className="hover:text-white transition-colors">Algo Marketplace</Link></li>
            </ul>
          </div>

          {/* Column 4: Brokers */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Brokers</h4>
            <ul className="space-y-2.5">
              <li><Link href="#brokers" className="hover:text-white transition-colors">Binance Integration</Link></li>
              <li><Link href="#brokers" className="hover:text-white transition-colors">Bybit Derivatives</Link></li>
              <li><Link href="#brokers" className="hover:text-white transition-colors">Interactive Brokers</Link></li>
              <li><Link href="#brokers" className="hover:text-white transition-colors">OKX Web3 & Futures</Link></li>
              <li><Link href="#brokers" className="hover:text-white transition-colors">Broker Awards 2026</Link></li>
              <li><Link href="#brokers" className="hover:text-white transition-colors">Exchange Comparison</Link></li>
            </ul>
          </div>

          {/* Column 5: Verification & Safety */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Trust & Risk</h4>
            <ul className="space-y-2.5">
              <li><Link href="/proofs" className="hover:text-white transition-colors text-[#2962ff] font-medium flex items-center gap-1"><ShieldCheck size={13} /> Proof Registry</Link></li>
              <li><Link href="#methodology" className="hover:text-white transition-colors">6-Gate Risk Architecture</Link></li>
              <li><Link href="#security" className="hover:text-white transition-colors">Non-Custodial Keys</Link></li>
              <li><Link href="#security" className="hover:text-white transition-colors">SOC 2 Alignment</Link></li>
              <li><Link href="#security" className="hover:text-white transition-colors">GDPR Data Controls</Link></li>
              <li><Link href="/settings/verification" className="hover:text-white transition-colors">KYC Verification</Link></li>
            </ul>
          </div>

          {/* Column 6: Education & Company */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2.5">
              <li><Link href="/academy" className="hover:text-white transition-colors">Quant Academy</Link></li>
              <li><Link href="#methodology" className="hover:text-white transition-colors">Methodology Whitepaper</Link></li>
              <li><Link href="#pricing" className="hover:text-white transition-colors">Pricing & Plans</Link></li>
              <li><Link href="#faq" className="hover:text-white transition-colors">Trading FAQ</Link></li>
              <li><Link href="/dashboard" className="hover:text-white transition-colors">Terminal Launch</Link></li>
              <li><Link href="/proofs" className="hover:text-white transition-colors">System Status: 99.98%</Link></li>
            </ul>
          </div>

        </div>

        {/* Compliance Badges & Disclosures Matching TradingView Footer */}
        <div className="pt-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#2962ff] flex items-center justify-center text-white font-bold">
              <Terminal size={16} />
            </div>
            <div>
              <div className="text-sm font-bold text-white uppercase tracking-tight">AlphaForge Inc.</div>
              <div className="text-[11px] text-[#787b86]">Made for autonomous quantitative intelligence</div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1 text-[#089981] font-semibold">
              <CheckCircle2 size={13} /> SOC 2 Compliant
            </span>
            <span className="flex items-center gap-1 text-[#089981] font-semibold">
              <CheckCircle2 size={13} /> GDPR Compliant
            </span>
            <span className="text-[#787b86]">|</span>
            <span className="text-[#787b86]">Market data provided by ICE Data Services & Binance WS</span>
          </div>
        </div>

        {/* Mandatory Regulatory Risk Warning */}
        <div className="mt-8 pt-6 border-t border-[#2a2e39]/60 text-[10px] text-[#787b86] leading-relaxed">
          <p>
            <strong className="text-[#b2b5be]">Risk Warning:</strong> Trading spot digital assets, forex, equities, and derivative contracts involves substantial risk of loss and is not suitable for all investors. Mathematical models, machine-learning signals, and backtested performance metrics do not guarantee future returns. AlphaForge provides pre-trade algorithmic execution assistance and quantitative analytics; it does not operate as an investment advisor, exchange, or custodian. Always manage leverage conservatively.
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
            <div>© {new Date().getFullYear()} AlphaForge Inc. All rights reserved.</div>
            <div className="flex items-center gap-4">
              <Link href="/terms" className="hover:text-white transition-colors">Terms of Use</Link>
              <Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
              <Link href="/disclaimer" className="hover:text-white transition-colors">Risk Disclosures</Link>
              <Link href="/proofs" className="hover:text-white transition-colors text-[#2962ff]">Cryptographic Registry</Link>
            </div>
          </div>
        </div>

      </div>
    </footer>
  );
}
