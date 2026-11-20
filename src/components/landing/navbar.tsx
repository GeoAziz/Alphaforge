'use client';

import { useState, useRef, useEffect, type FocusEvent } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useMarketData } from '@/providers/market-data-provider';
import { MAIN_NAV_MENU, type NavMenuItem } from './navigation-data';
import { cn } from '@/lib/utils';

// Helper icon renderer matching TradingView's exact 18px line icons
function MenuIcon({ name, icon }: { name: string; icon?: string }) {
  if (icon === 'diamond') {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white shrink-0">
        <path d="M6 3h12l4 6-10 12L2 9z" />
      </svg>
    );
  }

  const lower = name.toLowerCase();
  if (lower === 'entire world' || lower.includes('world')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    );
  }
  if (lower.includes('countries') || lower.includes('country')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
        <line x1="4" y1="22" x2="4" y2="15" />
      </svg>
    );
  }
  if (lower.includes('news')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
        <path d="M18 14h-8" />
        <path d="M15 18h-5" />
        <path d="M10 6h8v4h-8V6Z" />
      </svg>
    );
  }
  if (lower.includes('screener')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <circle cx="12" cy="12" r="10" />
        <line x1="22" y1="12" x2="18" y2="12" />
        <line x1="6" y1="12" x2="2" y2="12" />
        <line x1="12" y1="6" x2="12" y2="2" />
        <line x1="12" y1="22" x2="12" y2="18" />
      </svg>
    );
  }
  if (lower.includes('calendar')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    );
  }
  if (lower.includes('portfolio')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
      </svg>
    );
  }
  if (lower.includes('yield') || lower.includes('graph')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    );
  }
  if (lower.includes('option')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <line x1="6" y1="3" x2="6" y2="15" />
        <circle cx="18" cy="6" r="3" />
        <circle cx="6" cy="18" r="3" />
        <path d="M18 9a9 9 0 0 1-9 9" />
      </svg>
    );
  }
  if (lower.includes('map')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
        <line x1="8" y1="2" x2="8" y2="18" />
        <line x1="16" y1="6" x2="16" y2="22" />
      </svg>
    );
  }
  if (lower.includes('crypto')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.5 9h5a2 2 0 0 1 0 4h-5m0 0h5.5a2.5 2.5 0 0 1 0 5H9.5m0-9v12m2.5-14v2m0 12v2" />
      </svg>
    );
  }
  if (lower.includes('stock') || lower.includes('indices') || lower.includes('asset') || lower.includes('all markets')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    );
  }
  if (lower.includes('download') || lower.includes('desktop') || lower.includes('mobile')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
    );
  }
  if (lower.includes('business') || lower.includes('charting')) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#868993] group-hover:text-white shrink-0">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    );
  }
  return null;
}

// Fallback colored initials icon for watchlist assets
function WatchlistLogo({ title, logoUrl }: { title: string; logoUrl?: string }) {
  if (logoUrl) {
    return (
      <Image 
        src={logoUrl} 
        alt={title} 
        width={20} 
        height={20} 
        unoptimized
        className="w-5 h-5 rounded-full object-contain shrink-0" 
      />
    );
  }
  const colors = ['bg-[#f23645]', ['bg-[#2962ff]'], ['bg-[#089981]'], ['bg-[#ff9800]'], ['bg-[#9c27b0]']];
  const charCode = title.charCodeAt(0) || 0;
  const color = colors[charCode % colors.length];

  return (
    <div className={cn("w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0", color)}>
      {title.slice(0, 1)}
    </div>
  );
}

export function LandingNavbar() {
  const { isConnected, isStale } = useMarketData();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
  const [expandedMobileCategories, setExpandedMobileCategories] = useState<Record<string, boolean>>({
    markets: true,
  });
  const [expandedMobileItems, setExpandedMobileItems] = useState<Record<string, boolean>>({});

  const dropdownTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const submenuTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const headerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setSearchOpen(false);
        setActiveDropdown(null);
        setActiveSubmenu(null);
        setMobileMenuOpen(false);
      }
    };
    const handlePointerDown = (e: PointerEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setActiveDropdown(null);
        setActiveSubmenu(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('pointerdown', handlePointerDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('pointerdown', handlePointerDown);
      if (dropdownTimeoutRef.current) clearTimeout(dropdownTimeoutRef.current);
      if (submenuTimeoutRef.current) clearTimeout(submenuTimeoutRef.current);
    };
  }, []);

  const handleMouseEnter = (catId: string) => {
    if (dropdownTimeoutRef.current) clearTimeout(dropdownTimeoutRef.current);
    if (submenuTimeoutRef.current) clearTimeout(submenuTimeoutRef.current);
    setActiveDropdown(catId);
  };

  const handleMouseLeave = () => {
    dropdownTimeoutRef.current = setTimeout(() => {
      setActiveDropdown(null);
      setActiveSubmenu(null);
    }, 180);
  };

  const handleSubmenuEnter = (submenuId: string) => {
    if (submenuTimeoutRef.current) clearTimeout(submenuTimeoutRef.current);
    setActiveSubmenu(submenuId);
  };

  const handleSubmenuLeave = () => {
    submenuTimeoutRef.current = setTimeout(() => {
      setActiveSubmenu(null);
    }, 140);
  };

  const handlePrimaryFocus = (event: FocusEvent<HTMLLIElement>, catId: string) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      handleMouseEnter(catId);
    }
  };

  const getSubmenuId = (categoryId: string, sectionIndex: number, itemIndex: number) =>
    `${categoryId}:${sectionIndex}:${itemIndex}`;

  const closeMenus = () => {
    setActiveDropdown(null);
    setActiveSubmenu(null);
    setMobileMenuOpen(false);
  };

  const toggleMobileCategory = (catId: string) => {
    setExpandedMobileCategories(prev => ({
      ...prev,
      [catId]: !prev[catId],
    }));
  };

  const toggleMobileItem = (itemId: string) => {
    setExpandedMobileItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  // Searchable sample symbols
  const searchResults = [
    { symbol: 'BTC/USDT', name: 'Bitcoin / TetherUS', type: 'Crypto', price: '$68,450.20', change: '+3.42%' },
    { symbol: 'ETH/USDT', name: 'Ethereum / TetherUS', type: 'Crypto', price: '$3,540.80', change: '-1.15%' },
    { symbol: 'SOL/USDT', name: 'Solana / TetherUS', type: 'Crypto', price: '$184.60', change: '+5.82%' },
    { symbol: 'SPX', name: 'S&P 500 Index', type: 'Index', price: '5,885.20', change: '+0.44%' },
    { symbol: 'NDX', name: 'Nasdaq 100 Index', type: 'Index', price: '20,450.10', change: '+0.72%' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation', type: 'Stock', price: '$142.80', change: '+2.18%' },
    { symbol: 'EUR/USD', name: 'Euro / US Dollar', type: 'Forex', price: '1.0845', change: '+0.12%' },
    { symbol: 'XAU/USD', name: 'Gold / US Dollar', type: 'Commodity', price: '$2,680.50', change: '+0.85%' },
  ].filter(item => 
    searchQuery === '' || 
    item.symbol.toLowerCase().includes(searchQuery.toLowerCase()) || 
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* 
        TradingView Exact Header Container:
        Sticky top, Height: 64px, Background: #131722, Border-b: #2a2e39
      */}
      <header 
        ref={headerRef} 
        className="sticky top-0 z-50 w-full h-16 bg-[#131722] border-b border-[#2a2e39] text-[#d1d4dc] select-none font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]"
      >
        <div className="w-full h-full max-w-[2360px] mx-auto px-4 sm:px-6 md:px-8 xl:px-10 flex items-center justify-between">
          
          {/* ========================================================== */}
          {/* AREA 1: HAMBURGER + LOGO (TradingView .tv-header__area--logo-menu) */}
          {/* ========================================================== */}
          <div className="flex items-center shrink-0">
            {/* Mobile / Tablet Hamburger Button */}
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 -ml-2 mr-2 rounded-full text-[#d1d4dc] hover:bg-[#2a2e39]/80 hover:text-white transition-colors"
              aria-label="Open menu"
              aria-expanded={mobileMenuOpen}
              aria-haspopup="true"
            >
              <svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor">
                <path d="M0 12h18v-2h-18v2zm0-5h18v-2h-18v2zm0-7v2h18v-2h-18z" />
              </svg>
            </button>

            {/* TradingView Wordmark & Logo Mark */}
            <Link href="/" className="flex items-center gap-2.5 group cursor-pointer py-1">
              <div className="w-8 h-8 rounded-lg bg-[#2962ff] flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
                <svg width="22" height="17" viewBox="0 0 36 28" fill="currentColor">
                  <path d="M14 22H7V11H0V4h14v18zM28 22h-8l7.5-18h8L28 22z" />
                  <circle cx="20" cy="8" r="4" />
                </svg>
              </div>
              <span className="font-extrabold text-[20px] tracking-[-0.035em] text-white">
                Alpha<span className="text-[#2962ff]">Forge</span>
              </span>
            </Link>
          </div>

          {/* ========================================================== */}
          {/* AREA 2: SEARCH CONTAINER (TradingView .tv-header__area--search) */}
          {/* ========================================================== */}
          <div className="hidden md:flex items-center mx-4 lg:mx-6">
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center justify-between h-9 w-[220px] lg:w-[260px] px-3 rounded-full bg-[#1e222d] hover:bg-[#2a2e39] text-[#787b86] hover:text-[#d1d4dc] transition-all cursor-pointer border border-transparent hover:border-[#363a45]"
              aria-label="Search"
            >
              <div className="flex items-center gap-2">
                <svg width="18" height="18" viewBox="0 0 28 28" fill="currentColor" className="text-[#787b86] shrink-0">
                  <path fillRule="evenodd" d="M17.41 18.47a8.18 8.18 0 1 1 1.06-1.06L24 22.94 22.94 24zm1.45-6.29a6.68 6.68 0 1 1-13.36 0 6.68 6.68 0 0 1 13.36 0" />
                </svg>
                <span className="text-[13px] font-normal leading-6 tracking-normal">Search (Ctrl+K)</span>
              </div>
            </button>
          </div>

          {/* ========================================================== */}
          {/* AREA 3: MAIN NAVIGATION MENU (TradingView .tv-header__area--menu) */}
          {/* ========================================================== */}
          <nav className="hidden lg:flex items-center text-[14px] font-[500] leading-6 tracking-[0.2px] text-[#d1d4dc]">
            <ul className="flex items-center list-none m-0 p-0 gap-1">
              {MAIN_NAV_MENU.map((category) => {
                const isOpen = activeDropdown === category.id;
                return (
                  <li
                    key={category.id}
                    className="relative flex items-center"
                    onMouseEnter={() => handleMouseEnter(category.id)}
                    onMouseLeave={handleMouseLeave}
                    onFocus={(event) => handlePrimaryFocus(event, category.id)}
                  >
                    <Link
                      href={category.url}
                      aria-haspopup="menu"
                      aria-expanded={isOpen}
                      className={cn(
                        "flex items-center h-9 px-3.5 rounded-[36px] transition-colors duration-150 whitespace-nowrap cursor-pointer select-none focus-visible:outline-none",
                        isOpen
                          ? "bg-[#2a2e39] text-white"
                          : "hover:bg-[#2a2e39]/60 hover:text-white text-[#d1d4dc]"
                      )}
                    >
                      <span>{category.name}</span>
                    </Link>

                    {/* Exact TradingView Single-Column Vertical Dropdown Card */}
                    {isOpen && (
                      <div
                        className="absolute top-[calc(100%-2px)] left-0 z-50 pt-1.5 origin-top-left animate-in fade-in-50 zoom-in-95 duration-150 motion-reduce:animate-none w-[260px]"
                        role="menu"
                        aria-label={`${category.name} options`}
                        onMouseEnter={() => handleMouseEnter(category.id)}
                        onMouseLeave={handleMouseLeave}
                      >
                        <div className="bg-[#1e222d] border border-[#2a2e39] rounded-2xl shadow-[0_12px_36px_rgba(0,0,0,0.5)] p-2 backdrop-blur-xl">
                          {category.sections.map((section, sIdx) => (
                            <div key={sIdx} className={cn(sIdx > 0 && "mt-2 pt-2 border-t border-[#2a2e39]/60")}>
                              {section.title && (
                                <div className="text-[10px] font-bold uppercase tracking-wider text-[#787b86] px-3 py-1">
                                  {section.title}
                                </div>
                              )}
                              <div className="space-y-0.5">
                                {section.items.map((item, itemIdx) => {
                                  const submenuId = getSubmenuId(category.id, sIdx, itemIdx);
                                  const hasSubmenu = Boolean(item.subGroups?.length || item.watchlists?.length);
                                  const isSubmenuOpen = activeSubmenu === submenuId;
                                  const isFlagship = Boolean(item.subtitle);

                                  return (
                                    <div
                                      key={itemIdx}
                                      className="relative"
                                      onMouseEnter={() => hasSubmenu && handleSubmenuEnter(submenuId)}
                                      onMouseLeave={hasSubmenu ? handleSubmenuLeave : undefined}
                                      onFocus={(event) => {
                                        if (
                                          hasSubmenu &&
                                          !event.currentTarget.contains(event.relatedTarget as Node | null)
                                        ) {
                                          handleSubmenuEnter(submenuId);
                                        }
                                      }}
                                    >
                                      <Link
                                        href={item.url}
                                        onClick={closeMenus}
                                        role="menuitem"
                                        aria-haspopup={hasSubmenu ? 'menu' : undefined}
                                        aria-expanded={hasSubmenu ? isSubmenuOpen : undefined}
                                        className={cn(
                                          "group flex items-center justify-between px-3 py-2 rounded-xl text-[14px] transition-colors duration-150 focus-visible:outline-none",
                                          isSubmenuOpen
                                            ? "bg-[#2a2e39] text-white"
                                            : "text-[#d1d4dc] hover:text-white hover:bg-[#2a2e39]"
                                        )}
                                      >
                                        <div className="flex items-center gap-2.5 min-w-0">
                                          <MenuIcon name={item.name} icon={item.icon} />
                                          <div className="flex flex-col min-w-0">
                                            <span className={cn(
                                              "truncate font-normal",
                                              isFlagship && "font-semibold text-white"
                                            )}>
                                              {item.name}
                                            </span>
                                            {item.subtitle && (
                                              <span className="text-[11px] text-[#787b86] font-normal truncate mt-0.5">
                                                {item.subtitle}
                                              </span>
                                            )}
                                          </div>
                                        </div>

                                        <div className="flex items-center gap-1 shrink-0 ml-2">
                                          {item.badge && (
                                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#2962ff]/20 text-[#2962ff] uppercase tracking-wider">
                                              {item.badge}
                                            </span>
                                          )}
                                          {hasSubmenu && (
                                            <svg width="12" height="12" viewBox="0 0 18 18" fill="currentColor" className="text-[#787b86] group-hover:text-white transition-colors">
                                              <path d="M6.71 3.92 11.17 9l-4.46 5.08-1.13-1L9.17 9 5.58 4.91l1.13-.99Z" />
                                            </svg>
                                          )}
                                        </div>
                                      </Link>

                                      {/* Secondary Tier-2 & Tier-3 Flyout Menu with Quotes Watchlists Panel */}
                                      {hasSubmenu && isSubmenuOpen && (
                                        <div
                                          role="menu"
                                          aria-label={`${item.name} options`}
                                          onMouseEnter={() => handleSubmenuEnter(submenuId)}
                                          onMouseLeave={handleSubmenuLeave}
                                          className={cn(
                                            "absolute left-full top-0 z-50 pl-1.5 origin-left animate-in fade-in-50 slide-in-from-left-1 duration-150 motion-reduce:animate-none",
                                            item.watchlists?.length ? "w-[480px]" : "w-64"
                                          )}
                                        >
                                          <div className={cn(
                                            "rounded-2xl border border-[#2a2e39] bg-[#1e222d] p-3 shadow-[0_12px_36px_rgba(0,0,0,0.5)] max-h-[460px] overflow-y-auto",
                                            item.watchlists?.length ? "grid grid-cols-2 gap-4" : "space-y-2"
                                          )}>
                                            {/* Column 1: Subgroup Navigation links */}
                                            <div className="space-y-3">
                                              {item.subGroups?.map((group, gIdx) => (
                                                <div key={gIdx} className="space-y-1">
                                                  {group.title && (
                                                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#787b86] px-3 pt-1 pb-0.5">
                                                      {group.title}
                                                    </div>
                                                  )}
                                                  {group.items.map((sub, subIdx) => (
                                                    <Link
                                                      key={subIdx}
                                                      href={sub.url}
                                                      role="menuitem"
                                                      onClick={closeMenus}
                                                      className="block rounded-lg px-3 py-1.5 text-[13px] text-[#d1d4dc] transition-colors duration-150 hover:bg-[#2a2e39] hover:text-white"
                                                    >
                                                      {sub.name}
                                                    </Link>
                                                  ))}
                                                </div>
                                              ))}
                                            </div>

                                            {/* Column 2: TradingView Quotes / Market Watchlist Cards */}
                                            {item.watchlists && item.watchlists.length > 0 && (
                                              <div className="space-y-2 border-l border-[#2a2e39]/60 pl-3">
                                                <div className="text-[10px] font-bold uppercase tracking-wider text-[#787b86] px-2 pt-1 pb-0.5">
                                                  Trending Quotes
                                                </div>
                                                <div className="space-y-1">
                                                  {item.watchlists.map((wl, wIdx) => (
                                                    <Link
                                                      key={wIdx}
                                                      href={wl.url}
                                                      role="menuitem"
                                                      onClick={closeMenus}
                                                      className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:bg-[#2a2e39] transition-colors group cursor-pointer"
                                                    >
                                                      <WatchlistLogo title={wl.title} logoUrl={wl.logoUrl} />
                                                      <div className="flex flex-col min-w-0">
                                                        <span className="text-[13px] font-medium text-white group-hover:text-[#2962ff] transition-colors truncate">
                                                          {wl.title}
                                                        </span>
                                                        <span className="text-[10px] text-[#787b86] font-mono truncate">
                                                          {wl.proName}
                                                        </span>
                                                      </div>
                                                    </Link>
                                                  ))}
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* ========================================================== */}
          {/* AREA 4: USER & CTA AREA (TradingView .tv-header__area--user) */}
          {/* ========================================================== */}
          <div className="flex items-center gap-1 sm:gap-2 shrink-0">
            {/* Small screen icon search button */}
            <button
              onClick={() => setSearchOpen(true)}
              className="md:hidden p-2 rounded-full text-[#787b86] hover:text-white hover:bg-[#2a2e39] transition-colors"
              aria-label="Search"
            >
              <svg width="20" height="20" viewBox="0 0 28 28" fill="currentColor">
                <path fillRule="evenodd" d="M17.41 18.47a8.18 8.18 0 1 1 1.06-1.06L24 22.94 22.94 24zm1.45-6.29a6.68 6.68 0 1 1-13.36 0 6.68 6.68 0 0 1 13.36 0" />
              </svg>
            </button>

            {/* Live WS Telemetry Indicator */}
            <div className="hidden 2xl:flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1e222d] border border-[#2a2e39] text-[11px] font-mono mr-1">
              <span className={cn(
                'w-2 h-2 rounded-full animate-pulse',
                isConnected && !isStale ? 'bg-[#089981]' : isStale ? 'bg-amber-400' : 'bg-[#f23645]'
              )} />
              <span className="text-[#b2b5be]">
                {isConnected && !isStale ? 'WS 20ms' : isStale ? 'STALE' : 'OFFLINE'}
              </span>
            </div>

            {/* Language Selector (.tv-header__language-button) */}
            <button 
              className="flex items-center gap-1 h-9 px-3 rounded-[36px] text-[13px] font-bold text-[#b2b5be] hover:text-white hover:bg-[#2a2e39] transition-all cursor-pointer"
              aria-label="Open language menu"
            >
              <svg width="20" height="20" viewBox="0 0 28 28" fill="currentColor" className="shrink-0 text-[#787b86]">
                <path fillRule="evenodd" d="M12.1 4.69a9.54 9.54 0 0 1 3.8 0c.52 1.13.95 2.65 1.23 4.42a12.5 12.5 0 0 1-6.26 0c.28-1.77.71-3.29 1.23-4.42Zm-1.84.57a9.52 9.52 0 0 0-3.04 2.08c.63.51 1.38.95 2.2 1.3.22-1.25.5-2.39.84-3.38Zm-1.05 4.9c-1.1-.42-2.1-.98-2.95-1.67a9.46 9.46 0 0 0 0 11.03c.86-.68 1.86-1.24 2.96-1.66a33.91 33.91 0 0 1 0-7.7Zm.22 9.23c-.82.34-1.56.78-2.2 1.28a9.52 9.52 0 0 0 3.03 2.07 21.2 21.2 0 0 1-.83-3.35Zm2.67 3.92a17.46 17.46 0 0 1-1.23-4.4 12.2 12.2 0 0 1 6.26 0 17.46 17.46 0 0 1-1.23 4.4 9.54 9.54 0 0 1-3.8 0Zm5.64-.57a9.52 9.52 0 0 0 3.03-2.07 9.62 9.62 0 0 0-2.2-1.28 21.2 21.2 0 0 1-.83 3.35Zm1.04-4.88c1.1.42 2.1.98 2.95 1.66a9.46 9.46 0 0 0 .01-11.03c-.85.7-1.85 1.25-2.95 1.67a33.93 33.93 0 0 1 0 7.7Zm-1.45-7.25a14.06 14.06 0 0 1-6.66 0 32.64 32.64 0 0 0 0 6.8 13.74 13.74 0 0 1 6.66 0 32.62 32.62 0 0 0 0-6.8Zm1.24-1.98a9.1 9.1 0 0 0 2.2-1.29 9.52 9.52 0 0 0-3.03-2.08c.34 1 .62 2.13.83 3.37ZM14 3a11 11 0 1 0 0 22 11 11 0 0 0 0-22Z" />
              </svg>
              <span>EN</span>
            </button>

            {/* User Account Silhouette Button */}
            <Link 
              href="/login"
              className="w-10 h-10 rounded-full flex items-center justify-center text-[#d1d4dc] hover:text-white hover:bg-[#2a2e39] transition-all cursor-pointer"
              title="User Account"
              aria-label="Open user menu"
            >
              <svg width="22" height="22" viewBox="0 0 28 28" fill="currentColor">
                <path fillRule="evenodd" d="M17.5 9c0 1.14-.3 1.99-.79 2.54-.46.52-1.27.96-2.71.96s-2.25-.44-2.71-.96A3.74 3.74 0 0 1 10.5 9c0-1.14.3-1.99.79-2.54.46-.52 1.27-.96 2.71-.96s2.25.44 2.71.96c.5.55.79 1.4.79 2.54zM19 9c0 2.76-1.45 5-5 5s-5-2.24-5-5 1.45-5 5-5 5 2.24 5 5zm-8 8.5h6c2.04 0 3.1.5 3.76 1.1.69.63 1.11 1.55 1.5 2.8.13.42.04.95-.29 1.4-.33.46-.8.7-1.22.7H7.25c-.43 0-.89-.24-1.22-.7a1.61 1.61 0 0 1-.3-1.4 6.08 6.08 0 0 1 1.51-2.8c.65-.6 1.72-1.1 3.76-1.1zm6-1.5h-6c-4.6 0-5.88 2.33-6.7 4.96-.58 1.89.97 4.04 2.95 4.04h13.5c1.98 0 3.53-2.15 2.95-4.04C22.88 18.33 21.6 16 17 16z" />
              </svg>
            </Link>

            {/* TradingView Exact "Get started" Pill Button */}
            <Link href="/register" className="ml-1 sm:ml-2">
              <button className="h-10 px-5 rounded-full bg-white text-black hover:bg-[#e0e3eb] active:bg-[#d1d4dc] font-bold text-[14px] leading-5 tracking-tight transition-all shadow-sm active:scale-95 cursor-pointer flex items-center justify-center whitespace-nowrap">
                Get started
              </button>
            </Link>
          </div>

        </div>
      </header>

      {/* ========================================================== */}
      {/* MOBILE DRAWER ACCORDION NAVIGATION                         */}
      {/* ========================================================== */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div 
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={closeMenus}
          />
          <div className="relative w-4/5 max-w-sm bg-[#131722] border-r border-[#2a2e39] h-full overflow-y-auto p-5 text-[#d1d4dc] flex flex-col justify-between shadow-2xl">
            <div>
              {/* Drawer Top Header */}
              <div className="flex items-center justify-between pb-4 border-b border-[#2a2e39] mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 bg-[#2962ff] rounded-lg flex items-center justify-center text-white font-bold text-xs">
                    AF
                  </div>
                  <span className="font-extrabold text-lg text-white">AlphaForge</span>
                </div>
                <button
                  onClick={closeMenus}
                  className="p-1.5 rounded-lg text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
                  aria-label="Close menu"
                >
                  ✕
                </button>
              </div>

              {/* Multi-Level Accordion Categories */}
              <div className="space-y-4">
                {MAIN_NAV_MENU.map((category) => {
                  const isCatExpanded = Boolean(expandedMobileCategories[category.id]);
                  return (
                    <div key={category.id} className="border-b border-[#2a2e39]/40 pb-3">
                      {/* Category Header with Toggle */}
                      <button
                        onClick={() => toggleMobileCategory(category.id)}
                        className="w-full flex items-center justify-between py-2 text-left text-[15px] font-bold text-white hover:text-[#2962ff] transition-colors"
                      >
                        <span>{category.name}</span>
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 18 18"
                          className={cn("text-[#787b86] transition-transform duration-200", isCatExpanded && "rotate-180")}
                          fill="currentColor"
                        >
                          <path d="M3.92 7.83 9 12.29l5.08-4.46-1-1.13L9 10.29l-4.09-3.6-.99 1.14Z" />
                        </svg>
                      </button>

                      {/* Category Items */}
                      {isCatExpanded && (
                        <div className="mt-2 space-y-3 pl-2">
                          {category.sections.map((section, sIdx) => (
                            <div key={sIdx} className="space-y-1">
                              {section.title && (
                                <div className="text-[10px] font-bold uppercase tracking-wider text-[#787b86] px-2 pt-1">
                                  {section.title}
                                </div>
                              )}
                              {section.items.map((item, itemIdx) => {
                                const mobileItemId = `${category.id}:${sIdx}:${itemIdx}`;
                                const hasSubmenu = Boolean(item.subGroups?.length || item.watchlists?.length);
                                const isItemExpanded = Boolean(expandedMobileItems[mobileItemId]);
                                return (
                                  <div key={itemIdx} className="space-y-1">
                                    <div className="flex items-center justify-between">
                                      <Link
                                        href={item.url}
                                        onClick={closeMenus}
                                        className="flex-1 px-2 py-1.5 rounded-md text-[13px] text-[#b2b5be] hover:text-white hover:bg-[#2a2e39] transition-colors flex items-center gap-2"
                                      >
                                        <MenuIcon name={item.name} icon={item.icon} />
                                        <span>{item.name}</span>
                                      </Link>
                                      {hasSubmenu && (
                                        <button
                                          type="button"
                                          aria-label={`${item.name} submenu`}
                                          aria-expanded={isItemExpanded}
                                          onClick={() => toggleMobileItem(mobileItemId)}
                                          className="p-1.5 text-[#787b86] hover:text-white"
                                        >
                                          <svg 
                                            width="14" 
                                            height="14" 
                                            viewBox="0 0 18 18" 
                                            className={cn("transition-transform duration-200", isItemExpanded && "rotate-180")} 
                                            fill="currentColor"
                                          >
                                            <path d="M3.92 7.83 9 12.29l5.08-4.46-1-1.13L9 10.29l-4.09-3.6-.99 1.14Z" />
                                          </svg>
                                        </button>
                                      )}
                                    </div>

                                    {/* Level 3 Nested Submenu Accordion */}
                                    {hasSubmenu && isItemExpanded && (
                                      <div className="ml-3 pl-2 border-l border-[#2a2e39] space-y-2 py-1">
                                        {item.subGroups?.map((group, gIdx) => (
                                          <div key={gIdx} className="space-y-1">
                                            {group.title && (
                                              <div className="text-[9px] font-bold uppercase tracking-wider text-[#787b86] px-2 pt-0.5">
                                                {group.title}
                                              </div>
                                            )}
                                            {group.items.map((sub, subIdx) => (
                                              <Link
                                                key={subIdx}
                                                href={sub.url}
                                                onClick={closeMenus}
                                                className="block px-2 py-1 text-[12px] text-[#787b86] hover:text-white hover:bg-[#2a2e39]/50 rounded transition-colors"
                                              >
                                                {sub.name}
                                              </Link>
                                            ))}
                                          </div>
                                        ))}

                                        {/* Watchlists on mobile */}
                                        {item.watchlists && item.watchlists.length > 0 && (
                                          <div className="space-y-1 pt-1">
                                            <div className="text-[9px] font-bold uppercase tracking-wider text-[#787b86] px-2">
                                              Trending Quotes
                                            </div>
                                            {item.watchlists.map((wl, wIdx) => (
                                              <Link
                                                key={wIdx}
                                                href={wl.url}
                                                onClick={closeMenus}
                                                className="flex items-center gap-2 px-2 py-1 text-[12px] text-white hover:bg-[#2a2e39]/50 rounded transition-colors"
                                              >
                                                <WatchlistLogo title={wl.title} logoUrl={wl.logoUrl} />
                                                <span className="truncate">{wl.title}</span>
                                              </Link>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Bottom Account & CTA Strip */}
            <div className="pt-6 border-t border-[#2a2e39] mt-6 space-y-3">
              <Link 
                href="/login"
                onClick={closeMenus}
                className="w-full h-10 flex items-center justify-center rounded-full border border-[#2a2e39] text-sm font-semibold hover:bg-[#2a2e39] transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                onClick={closeMenus}
                className="w-full h-10 flex items-center justify-center rounded-full bg-white text-black text-sm font-bold hover:bg-[#e0e3eb] transition-colors shadow-sm"
              >
                Get started
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* GLOBAL SEARCH MODAL (TradingView Symbol & Tool Search)     */}
      {/* ========================================================== */}
      {searchOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-start justify-center pt-20 px-4 font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]"
          onClick={() => setSearchOpen(false)}
        >
          <div 
            className="w-full max-w-xl rounded-2xl border border-[#2a2e39] bg-[#1e222d] shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center px-4 py-3.5 border-b border-[#2a2e39]">
              <svg width="20" height="20" viewBox="0 0 28 28" fill="currentColor" className="text-[#787b86] mr-3">
                <path fillRule="evenodd" d="M17.41 18.47a8.18 8.18 0 1 1 1.06-1.06L24 22.94 22.94 24zm1.45-6.29a6.68 6.68 0 1 1-13.36 0 6.68 6.68 0 0 1 13.36 0" />
              </svg>
              <input
                autoFocus
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search markets, symbols, strategies..."
                className="w-full bg-transparent text-sm text-white focus:outline-none placeholder:text-[#787b86]"
              />
              <button 
                onClick={() => setSearchOpen(false)}
                className="text-xs text-[#787b86] hover:text-white px-2 py-1 rounded bg-[#2a2e39]"
              >
                ESC
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto divide-y divide-[#2a2e39]/50 p-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#787b86] px-3 py-1.5">
                Popular Instruments
              </div>
              {searchResults.map((item, idx) => (
                <Link
                  key={idx}
                  href={`/dashboard?symbol=${encodeURIComponent(item.symbol)}`}
                  onClick={() => setSearchOpen(false)}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-[#2a2e39] transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-lg bg-[#131722] flex items-center justify-center font-bold text-xs text-white">
                      {item.symbol.slice(0, 3)}
                    </span>
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-[#2962ff] transition-colors flex items-center gap-1.5">
                        {item.symbol}
                        <span className="text-[10px] font-normal text-[#787b86] px-1.5 py-0.5 rounded bg-[#131722]">
                          {item.type}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#787b86]">{item.name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono font-bold text-white">{item.price}</div>
                    <div className={cn(
                      "text-[10px] font-mono font-bold",
                      item.change.startsWith('+') ? "text-[#089981]" : "text-[#f23645]"
                    )}>
                      {item.change}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            
            <div className="px-4 py-2.5 border-t border-[#2a2e39] bg-[#131722] flex items-center justify-between text-[11px] text-[#787b86]">
              <span>Press <kbd className="font-mono text-white">Enter</kbd> to open in Terminal</span>
              <Link href="/dashboard" className="text-[#2962ff] hover:underline flex items-center gap-1">
                Full Screener →
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
