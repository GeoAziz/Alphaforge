'use client';

import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  SlidersHorizontal, 
  Activity, 
  Bell, 
  Play, 
  Undo2, 
  Redo2, 
  Grid2X2, 
  Cloud, 
  Settings, 
  Maximize2, 
  Camera,
  ChevronDown
} from 'lucide-react';
import { ChartInstrument, ChartStyleType } from '@/lib/charting/types';
import { cn } from '@/lib/utils';

interface TopToolbarProps {
  activeInstrument: ChartInstrument;
  activeInterval: string;
  activeStyle: ChartStyleType;
  showRSI: boolean;
  onSymbolClick: () => void;
  onIntervalChange: (interval: string) => void;
  onStyleChange: (style: ChartStyleType) => void;
  onToggleRSI: () => void;
  onOpenAlertModal: () => void;
  onToggleReplay: () => void;
  onOpenSettings: () => void;
  onFullscreen: () => void;
  onTakeScreenshot: () => void;
}

const TIMEFRAMES = ['1m', '5m', '15m', '1H', '4H', '1D', '1W'];

export function TopToolbar({
  activeInstrument,
  activeInterval,
  activeStyle,
  showRSI,
  onSymbolClick,
  onIntervalChange,
  onStyleChange,
  onToggleRSI,
  onOpenAlertModal,
  onToggleReplay,
  onOpenSettings,
  onFullscreen,
  onTakeScreenshot,
}: TopToolbarProps) {
  const [styleDropdownOpen, setStyleDropdownOpen] = useState(false);

  return (
    <div className="h-12 border-b border-[#2a2e39] bg-[#1e222d] px-3 flex items-center justify-between shrink-0 select-none z-20">
      {/* Left: Brand + Symbol + Intervals + Styles + Indicators */}
      <div className="flex items-center gap-1.5">
        {/* Brand Watermark Badge */}
        <div className="flex items-center gap-1.5 mr-2">
          <div className="w-5 h-5 rounded bg-[#2962ff] flex items-center justify-center font-black text-white text-[11px]">
            α
          </div>
          <span className="font-bold text-xs tracking-wider text-white hidden sm:inline">ALPHAFORGE</span>
        </div>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        {/* Symbol Selector */}
        <button
          onClick={onSymbolClick}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-[#2a2e39]/60 hover:bg-[#2a2e39] text-white transition-colors cursor-pointer"
        >
          <Search className="w-3.5 h-3.5 text-[#787b86]" />
          <span className="font-bold text-sm tracking-tight">{activeInstrument.ticker}</span>
          <span className="text-[10px] text-[#787b86] uppercase font-mono">{activeInstrument.exchange}</span>
          <ChevronDown className="w-3 h-3 text-[#787b86]" />
        </button>

        {/* Compare / Add Symbol Button */}
        <button 
          title="Compare or Add Symbol (+)"
          className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        {/* Timeframe Pills */}
        <div className="flex items-center gap-0.5">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => onIntervalChange(tf)}
              className={cn(
                "px-2 py-1 rounded text-xs font-semibold transition-colors",
                activeInterval === tf ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
              )}
            >
              {tf}
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        {/* Chart Style Selector */}
        <div className="relative">
          <button
            onClick={() => setStyleDropdownOpen(!styleDropdownOpen)}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs capitalize text-[#d1d4dc] hover:bg-[#2a2e39]"
          >
            <span>{activeStyle}</span>
            <ChevronDown className="w-3 h-3 text-[#787b86]" />
          </button>

          {styleDropdownOpen && (
            <div className="absolute top-8 left-0 w-36 bg-[#1e222d] border border-[#2a2e39] rounded shadow-xl py-1 z-50">
              {(['candlestick', 'bar', 'area', 'line'] as ChartStyleType[]).map((style) => (
                <button
                  key={style}
                  onClick={() => {
                    onStyleChange(style);
                    setStyleDropdownOpen(false);
                  }}
                  className={cn(
                    "w-full text-left px-3 py-1.5 text-xs capitalize hover:bg-[#2a2e39]",
                    activeStyle === style ? "text-[#2962ff] font-bold" : "text-[#d1d4dc]"
                  )}
                >
                  {style}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        {/* Indicators Dialog Trigger */}
        <button
          onClick={onToggleRSI}
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition-colors",
            showRSI ? "bg-[#7e57c2]/20 text-[#b39ddb] border border-[#7e57c2]/40" : "text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
          )}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Indicators {showRSI ? '(1)' : ''}</span>
        </button>

        {/* Price Alert Button */}
        <button
          onClick={onOpenAlertModal}
          className="flex items-center gap-1 px-2 py-1 rounded text-xs text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
          title="Create Price Alert"
        >
          <Bell className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Alert</span>
        </button>

        {/* Bar Replay Trigger */}
        <button
          onClick={onToggleReplay}
          className="flex items-center gap-1 px-2 py-1 rounded text-xs text-[#787b86] hover:text-white hover:bg-[#2a2e39]"
          title="Bar Replay Simulation"
        >
          <Play className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Replay</span>
        </button>
      </div>

      {/* Right Controls: Undo/Redo, Layout, Cloud Save, Settings, Fullscreen, Screenshot */}
      <div className="flex items-center gap-1.5">
        <button className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Undo (Ctrl+Z)">
          <Undo2 className="w-3.5 h-3.5" />
        </button>
        <button className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Redo (Ctrl+Y)">
          <Redo2 className="w-3.5 h-3.5" />
        </button>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        <button className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Select Layout Grid">
          <Grid2X2 className="w-3.5 h-3.5" />
        </button>

        <button className="flex items-center gap-1 px-2 py-1 rounded bg-[#2a2e39]/60 hover:bg-[#2a2e39] text-xs font-semibold text-white">
          <Cloud className="w-3.5 h-3.5 text-[#089981]" />
          <span>Save</span>
        </button>

        <div className="h-4 w-px bg-[#2a2e39] mx-1" />

        <button onClick={onOpenSettings} className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Chart Properties (Settings)">
          <Settings className="w-3.5 h-3.5" />
        </button>

        <button onClick={onFullscreen} className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Fullscreen Mode">
          <Maximize2 className="w-3.5 h-3.5" />
        </button>

        <button onClick={onTakeScreenshot} className="p-1.5 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white" title="Take Screenshot">
          <Camera className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
