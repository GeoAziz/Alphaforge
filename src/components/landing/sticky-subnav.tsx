'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

export interface StickyNavTab {
  id: string;
  name: string;
}

const STICKY_TABS: StickyNavTab[] = [
  { id: 'supercharts', name: 'Supercharts' },
  { id: 'market-summary', name: 'Market summary' },
  { id: 'community-ideas', name: 'Community' },
  { id: 'stocks-hub', name: 'Stocks' },
  { id: 'crypto-hub', name: 'Crypto' },
  { id: 'futures-hub', name: 'Futures' },
  { id: 'forex-hub', name: 'Forex' },
  { id: 'brokers', name: 'Brokers' },
];

export function StickySubNav() {
  const [activeTab, setActiveTab] = useState('supercharts');

  useEffect(() => {
    const observerCallback: IntersectionObserverCallback = (entries) => {
      // Find the first visible entry
      const visible = entries.find((entry) => entry.isIntersecting);
      if (visible) {
        setActiveTab(visible.target.id);
      }
    };

    const observer = new IntersectionObserver(observerCallback, {
      root: null,
      rootMargin: '-80px 0px -60% 0px',
      threshold: 0,
    });

    STICKY_TABS.forEach((tab) => {
      const el = document.getElementById(tab.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    setActiveTab(id);
    const el = document.getElementById(id);
    if (el) {
      const yOffset = -120; // 64px header + 48px sticky bar + padding
      const y = el.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <nav
      aria-label="Market sections navigation"
      className="sticky top-16 z-40 w-full bg-[#131722]/95 backdrop-blur-md border-b border-[#2a2e39] font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]"
    >
      <div className="max-w-[2360px] mx-auto px-4 sm:px-6 md:px-8 xl:px-10">
        <div
          role="tablist"
          aria-orientation="horizontal"
          className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto py-2.5 no-scrollbar scroll-smooth"
        >
          {STICKY_TABS.map((tab) => {
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isSelected}
                onClick={() => scrollTo(tab.id)}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-[13px] font-medium leading-5 whitespace-nowrap transition-all duration-150 cursor-pointer shrink-0 select-none",
                  isSelected
                    ? "bg-white text-black font-semibold shadow-sm"
                    : "text-[#787b86] hover:text-white hover:bg-[#2a2e39]/60"
                )}
              >
                {tab.name}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
