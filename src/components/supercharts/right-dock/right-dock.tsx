'use client';

import React, { useState } from 'react';
import { 
  Bookmark, 
  Bell, 
  Newspaper, 
  Layers, 
  Flame, 
  Calendar,
  X,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { WatchlistSymbol, ChartInstrument } from '@/lib/charting/types';
import { cn } from '@/lib/utils';

export type DockTabType = 'watchlist' | 'alerts' | 'news' | 'data_window' | 'hotlists' | 'calendar';

interface RightDockProps {
  activeSymbol: string;
  instruments: ChartInstrument[];
  watchlistItems: WatchlistSymbol[];
  activeInstrument: ChartInstrument;
  onSelectSymbol: (symbol: string) => void;
}

export function RightDock({
  activeSymbol,
  instruments,
  watchlistItems,
  activeInstrument,
  onSelectSymbol,
}: RightDockProps) {
  const [activeTab, setActiveTab] = useState<DockTabType | null>('watchlist');
  const [activeWatchlistCategory, setActiveWatchlistCategory] = useState<'ALL' | 'INDICES' | 'STOCKS' | 'CRYPTO'>('ALL');

  const selectedItem = watchlistItems.find(i => i.symbol === activeInstrument.symbol) || watchlistItems[0];

  const filteredItems = activeWatchlistCategory === 'ALL'
    ? watchlistItems
    : watchlistItems.filter(i => i.category === activeWatchlistCategory);

  return (
    <div className="flex h-full shrink-0 select-none z-20">
      {/* 1. Expandable Content Drawer (320px) */}
      {activeTab && (
        <div className="w-80 border-l border-[#2a2e39] bg-[#1e222d] flex flex-col h-full overflow-hidden text-[#d1d4dc]">
          {/* Header */}
          <div className="h-10 border-b border-[#2a2e39] px-3 flex items-center justify-between shrink-0">
            <span className="text-xs font-bold uppercase tracking-wider text-white">
              {activeTab === 'watchlist' && 'Watchlist & Details'}
              {activeTab === 'alerts' && 'Alerts Manager'}
              {activeTab === 'news' && 'Live News Stream'}
              {activeTab === 'data_window' && 'Data Window'}
              {activeTab === 'hotlists' && 'Market Hotlists'}
              {activeTab === 'calendar' && 'Economic Calendar'}
            </span>
            <button
              onClick={() => setActiveTab(null)}
              className="p-1 rounded text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* TAB 1: WATCHLIST & SYMBOL INTEL */}
          {activeTab === 'watchlist' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Category Filter Pills */}
              <div className="flex items-center gap-1 px-3 py-2 border-b border-[#2a2e39] overflow-x-auto">
                {(['ALL', 'INDICES', 'STOCKS', 'CRYPTO'] as const).map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setActiveWatchlistCategory(cat)}
                    className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase transition-colors shrink-0",
                      activeWatchlistCategory === cat ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Table Header */}
              <div className="grid grid-cols-12 px-3 py-1.5 text-[10px] uppercase font-bold text-[#787b86] border-b border-[#2a2e39]">
                <div className="col-span-5">Symbol</div>
                <div className="col-span-4 text-right">Last</div>
                <div className="col-span-3 text-right">Chg%</div>
              </div>

              {/* Watchlist Symbol Rows */}
              <div className="flex-1 overflow-y-auto divide-y divide-[#2a2e39]/40">
                {filteredItems.map((item) => (
                  <button
                    key={item.symbol}
                    onClick={() => onSelectSymbol(item.symbol)}
                    className={cn(
                      "w-full grid grid-cols-12 px-3 py-2 items-center text-left text-xs transition-colors hover:bg-[#2a2e39]/60",
                      activeInstrument.symbol === item.symbol && "bg-[#2a2e39]"
                    )}
                  >
                    <div className="col-span-5">
                      <div className="font-bold text-white text-xs">{item.symbol}</div>
                      <div className="text-[10px] text-[#787b86] truncate">{item.name}</div>
                    </div>
                    <div className="col-span-4 text-right font-mono font-semibold text-white">
                      {item.price >= 1000 ? item.price.toLocaleString(undefined, { minimumFractionDigits: 2 }) : item.price.toFixed(item.price < 2 ? 4 : 2)}
                    </div>
                    <div className={cn(
                      "col-span-3 text-right font-mono font-bold text-[11px]",
                      item.isUp ? "text-[#089981]" : "text-[#f23645]"
                    )}>
                      {item.isUp ? `+${item.change24hPct}%` : `${item.change24hPct}%`}
                    </div>
                  </button>
                ))}
              </div>

              {/* ACTIVE SYMBOL FUNDAMENTAL INTEL CARD */}
              <div className="h-56 border-t border-[#2a2e39] bg-[#171b26] p-3 flex flex-col justify-between shrink-0 overflow-y-auto">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">{activeInstrument.name}</span>
                    <span className="text-[10px] font-mono text-[#787b86] uppercase">{activeInstrument.exchange}</span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-xl font-bold font-mono text-white">
                      ${selectedItem.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                    <span className={cn(
                      "text-xs font-mono font-bold",
                      selectedItem.isUp ? "text-[#089981]" : "text-[#f23645]"
                    )}>
                      {selectedItem.isUp ? `+${selectedItem.change24h}` : selectedItem.change24h} ({selectedItem.isUp ? `+${selectedItem.change24hPct}%` : `${selectedItem.change24hPct}%`})
                    </span>
                  </div>
                  {selectedItem.preMarketPrice && (
                    <div className="text-[11px] font-mono text-amber-400 mt-0.5">
                      Pre-market: ${selectedItem.preMarketPrice.toFixed(2)} (+{selectedItem.preMarketChangePct}%)
                    </div>
                  )}
                </div>

                <div className="text-[11px] text-[#787b86] line-clamp-3 bg-[#1e222d] p-2 rounded border border-[#2a2e39]/60">
                  {selectedItem.keyFacts || 'Leading market entity traded on global verified institutional exchanges with continuous liquidity.'}
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-[#787b86] pt-1 border-t border-[#2a2e39]/40">
                  <div>
                    <span>Vol: </span>
                    <span className="text-white font-bold">{(selectedItem.volume24h / 1000).toFixed(1)}K</span>
                  </div>
                  <div>
                    <span>Avg Vol (30D): </span>
                    <span className="text-white font-bold">{selectedItem.avgVolume30D ? `${(selectedItem.avgVolume30D / 1000).toFixed(1)}K` : '42.1K'}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ALERTS MANAGER */}
          {activeTab === 'alerts' && (
            <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto text-xs">
              <button className="w-full py-2 bg-[#2962ff] hover:bg-[#2962ff]/90 text-white font-bold rounded">
                + Create Price Alert
              </button>
              <div className="p-2.5 rounded bg-[#171b26] border border-[#2a2e39] flex flex-col gap-1">
                <div className="flex items-center justify-between font-bold text-white">
                  <span>{activeInstrument.ticker} &gt; 355.00</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#089981]/20 text-[#089981]">ACTIVE</span>
                </div>
                <span className="text-[11px] text-[#787b86]">Triggers once price crosses above 355.00 USD</span>
              </div>
            </div>
          )}

          {/* TAB 3: NEWS STREAM */}
          {activeTab === 'news' && (
            <div className="flex-1 p-3 flex flex-col gap-2 overflow-y-auto text-xs">
              <div className="p-2 rounded bg-[#171b26] border border-[#2a2e39] flex flex-col gap-1">
                <div className="flex items-center justify-between text-[10px] text-[#787b86]">
                  <span>Bloomberg · 12m ago</span>
                  <span className="text-[#089981] font-bold">BULLISH</span>
                </div>
                <div className="font-semibold text-white">Quarterly Earnings Beat Expectations Across Enterprise Segments</div>
              </div>
              <div className="p-2 rounded bg-[#171b26] border border-[#2a2e39] flex flex-col gap-1">
                <div className="flex items-center justify-between text-[10px] text-[#787b86]">
                  <span>Reuters · 1h ago</span>
                  <span className="text-[#787b86] font-bold">NEUTRAL</span>
                </div>
                <div className="font-semibold text-white">Global Supply Chains Stabilize Ahead of Central Bank Rate Decisions</div>
              </div>
            </div>
          )}

          {/* TAB 4: DATA WINDOW */}
          {activeTab === 'data_window' && (
            <div className="flex-1 p-3 flex flex-col gap-2 font-mono text-xs">
              <div className="text-[11px] text-[#787b86] uppercase font-bold border-b border-[#2a2e39] pb-1">Crosshair Inspector</div>
              <div className="flex justify-between"><span>Open:</span><span className="text-white">${selectedItem.price.toFixed(2)}</span></div>
              <div className="flex justify-between"><span>High:</span><span className="text-white">${(selectedItem.price * 1.01).toFixed(2)}</span></div>
              <div className="flex justify-between"><span>Low:</span><span className="text-white">${(selectedItem.price * 0.99).toFixed(2)}</span></div>
              <div className="flex justify-between"><span>Close:</span><span className="text-white">${selectedItem.price.toFixed(2)}</span></div>
              <div className="flex justify-between"><span>Volume:</span><span className="text-white">{selectedItem.volume24h.toLocaleString()}</span></div>
              <div className="flex justify-between"><span>RSI (14):</span><span className="text-[#b39ddb]">54.21</span></div>
            </div>
          )}

          {/* TAB 5: HOTLISTS */}
          {activeTab === 'hotlists' && (
            <div className="flex-1 p-3 flex flex-col gap-2 text-xs">
              <span className="text-[11px] text-[#787b86] font-bold uppercase">Top Gainers (24h)</span>
              <div className="flex justify-between items-center p-2 rounded bg-[#171b26]">
                <span className="font-bold text-white">SOL/USDT</span>
                <span className="font-mono text-[#089981] font-bold">+5.82%</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-[#171b26]">
                <span className="font-bold text-white">BTC/USDT</span>
                <span className="font-mono text-[#089981] font-bold">+3.42%</span>
              </div>
            </div>
          )}

          {/* TAB 6: CALENDAR */}
          {activeTab === 'calendar' && (
            <div className="flex-1 p-3 flex flex-col gap-2 text-xs">
              <span className="text-[11px] text-[#787b86] font-bold uppercase">Macro Economic Releases</span>
              <div className="p-2 rounded bg-[#171b26] border border-[#2a2e39] flex flex-col gap-1">
                <div className="flex justify-between text-[10px] text-amber-400 font-bold">
                  <span>US Non-Farm Payrolls</span>
                  <span>13:30 UTC</span>
                </div>
                <div className="text-[#787b86] text-[11px]">Forecast: 180K · Previous: 215K</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. Vertical Icon Strip (48px) */}
      <div className="w-12 border-l border-[#2a2e39] bg-[#1e222d] flex flex-col items-center py-2 gap-1 shrink-0">
        <button
          onClick={() => setActiveTab(activeTab === 'watchlist' ? null : 'watchlist')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'watchlist' && "text-white bg-[#2a2e39]"
          )}
          title="Watchlist & Details"
        >
          <Bookmark className="w-4 h-4" />
        </button>

        <button
          onClick={() => setActiveTab(activeTab === 'alerts' ? null : 'alerts')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'alerts' && "text-white bg-[#2a2e39]"
          )}
          title="Alerts Manager"
        >
          <Bell className="w-4 h-4" />
        </button>

        <button
          onClick={() => setActiveTab(activeTab === 'news' ? null : 'news')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'news' && "text-white bg-[#2a2e39]"
          )}
          title="News Stream"
        >
          <Newspaper className="w-4 h-4" />
        </button>

        <button
          onClick={() => setActiveTab(activeTab === 'data_window' ? null : 'data_window')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'data_window' && "text-white bg-[#2a2e39]"
          )}
          title="Data Window"
        >
          <Layers className="w-4 h-4" />
        </button>

        <button
          onClick={() => setActiveTab(activeTab === 'hotlists' ? null : 'hotlists')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'hotlists' && "text-white bg-[#2a2e39]"
          )}
          title="Market Hotlists"
        >
          <Flame className="w-4 h-4" />
        </button>

        <button
          onClick={() => setActiveTab(activeTab === 'calendar' ? null : 'calendar')}
          className={cn(
            "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
            activeTab === 'calendar' && "text-white bg-[#2a2e39]"
          )}
          title="Economic Calendar"
        >
          <Calendar className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
