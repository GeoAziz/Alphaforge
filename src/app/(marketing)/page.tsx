import { HeroBanner } from '@/components/landing/hero-banner';
import { StickySubNav } from '@/components/landing/sticky-subnav';
import { SuperchartsHero } from '@/components/landing/supercharts-hero';
import { MarketSummaryDashboard } from '@/components/landing/market-summary-dashboard';
import { CommunityIdeasSection } from '@/components/landing/community-ideas-section';
import { AssetHubsSection } from '@/components/landing/asset-hubs-section';
import { BrokersSection } from '@/components/landing/brokers-section';
import { MethodologySection } from '@/components/landing/methodology-section';
import { SecurityArchitecture } from '@/components/landing/security-architecture';
import { PricingMatrix } from '@/components/landing/pricing-matrix';
import { FAQSection } from '@/components/landing/faq-section';

export const metadata = {
  title: 'AlphaForge — Track All Markets & Quant Alpha',
  description: 'Where the world tracks markets, AI-powered quant signals, interactive Supercharts, and mathematically verified execution risk rules.',
};

export default function LandingPage() {
  return (
    <div className="space-y-0 bg-[#131722] text-[#d1d4dc] min-h-screen">
      {/* 1. Hero: "Where the world does markets" */}
      <HeroBanner />

      {/* 2. Sticky Sub-Nav Anchors matching TradingView sticky-navigation-tabs */}
      <StickySubNav />

      {/* 3. "Supercharged Supercharts" Live Interactive Chart Showcase */}
      <SuperchartsHero />

      {/* 4. Multi-Market Summary Dashboard: Indices, Crypto Totals, Futures & Yields */}
      <MarketSummaryDashboard />

      {/* 5. Community Ideas & Indicators/Strategies */}
      <CommunityIdeasSection />

      {/* 6. Deep Asset Hubs: US Stocks, Crypto Coins, Forex Rates & Macro Events */}
      <AssetHubsSection />

      {/* 7. Trading and Brokers: Direct Exchange Connectivity */}
      <BrokersSection />

      {/* 8. Quantitative Pipeline & 6-Gate Risk Architecture */}
      <MethodologySection />

      {/* 9. Zero-Trust API Security Architecture */}
      <SecurityArchitecture />

      {/* 10. Membership Tiers & Institutional Entitlements */}
      <PricingMatrix />

      {/* 11. Risk FAQ & Execution Disclosures */}
      <FAQSection />
    </div>
  );
}
