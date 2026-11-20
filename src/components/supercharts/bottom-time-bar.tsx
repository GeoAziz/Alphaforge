'use client';

import React from 'react';
import { RangePreset } from '@/lib/charting/range-calculator';
import { cn } from '@/lib/utils';
import { Calendar, Globe } from 'lucide-react';

interface BottomTimeBarProps {
  activeRange: RangePreset;
  timezone: string;
  scaleMode: 'normal' | 'log' | 'percentage';
  onSelectRange: (range: RangePreset) => void;
  onToggleScaleMode: (mode: 'normal' | 'log' | 'percentage') => void;
  onSelectTimezone: () => void;
}

const PRESETS: RangePreset[] = ['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'];

export function BottomTimeBar({
  activeRange,
  timezone,
  scaleMode,
  onSelectRange,
  onToggleScaleMode,
  onSelectTimezone,
}: BottomTimeBarProps) {
  return (
    <div className="h-8 border-t border-[#2a2e39] bg-[#1e222d] px-3 flex items-center justify-between shrink-0 select-none z-20 text-xs">
      {/* Left: Range Presets */}
      <div className="flex items-center gap-1">
        {PRESETS.map((p) => (
          <button
            key={p}
            onClick={() => onSelectRange(p)}
            className={cn(
              "px-2 py-0.5 rounded font-semibold transition-colors",
              activeRange === p ? "text-[#2962ff] bg-[#2962ff]/10 font-bold" : "text-[#787b86] hover:text-white"
            )}
          >
            {p}
          </button>
        ))}

        <div className="h-3 w-px bg-[#2a2e39] mx-1" />

        <button className="p-1 rounded text-[#787b86] hover:text-white hover:bg-[#2a2e39]" title="Go to Date (Calendar)">
          <Calendar className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Right: Timezone & Scale Controls */}
      <div className="flex items-center gap-2">
        {/* Clock & Timezone */}
        <button
          onClick={onSelectTimezone}
          className="flex items-center gap-1 text-[11px] font-mono text-[#787b86] hover:text-white"
        >
          <Globe className="w-3 h-3" />
          <span>{timezone}</span>
        </button>

        <div className="h-3 w-px bg-[#2a2e39] mx-1" />

        {/* Scale Mode Toggles */}
        <button
          onClick={() => onToggleScaleMode('percentage')}
          className={cn(
            "px-1.5 py-0.5 rounded text-[11px] font-bold uppercase transition-colors",
            scaleMode === 'percentage' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
          )}
        >
          %
        </button>

        <button
          onClick={() => onToggleScaleMode('log')}
          className={cn(
            "px-1.5 py-0.5 rounded text-[11px] font-bold uppercase transition-colors",
            scaleMode === 'log' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
          )}
        >
          log
        </button>

        <button
          onClick={() => onToggleScaleMode('normal')}
          className={cn(
            "px-1.5 py-0.5 rounded text-[11px] font-bold uppercase transition-colors",
            scaleMode === 'normal' ? "bg-[#2962ff] text-white" : "text-[#787b86] hover:text-white"
          )}
        >
          auto
        </button>
      </div>
    </div>
  );
}
