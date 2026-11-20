import React from 'react';
import { MarketDataProvider } from '@/providers/market-data-provider';
import { LandingNavbar } from '@/components/landing/navbar';
import { TickerTape } from '@/components/landing/ticker-tape';
import { LandingFooter } from '@/components/landing/footer';

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <MarketDataProvider>
      <div className="min-h-screen flex flex-col bg-background text-foreground noise-surface relative selection:bg-primary selection:text-primary-foreground">
        <LandingNavbar />
        <TickerTape />
        <main className="flex-1">{children}</main>
        <LandingFooter />
      </div>
    </MarketDataProvider>
  );
}
