'use client';

import React, { useState } from 'react';
import { 
  Crosshair, 
  TrendingUp, 
  SlidersHorizontal, 
  Square, 
  Type, 
  Activity, 
  Ruler, 
  Magnet, 
  Lock, 
  Eye, 
  Trash2,
  ChevronRight
} from 'lucide-react';
import { DrawingToolType } from '@/lib/charting/types';
import { cn } from '@/lib/utils';

interface DrawingToolbarProps {
  activeTool: DrawingToolType;
  magnetMode: 'off' | 'weak' | 'strong';
  onSelectTool: (tool: DrawingToolType) => void;
  onToggleMagnet: () => void;
  onDeleteSelected: () => void;
  onClearAll: () => void;
}

export function DrawingToolbar({
  activeTool,
  magnetMode,
  onSelectTool,
  onToggleMagnet,
  onDeleteSelected,
  onClearAll,
}: DrawingToolbarProps) {
  const [activeFlyout, setActiveFlyout] = useState<string | null>(null);

  return (
    <div className="w-12 border-r border-[#2a2e39] bg-[#1e222d] flex flex-col items-center py-2 gap-1 shrink-0 select-none z-20">
      {/* 1. Cursor / Crosshair */}
      <button
        onClick={() => onSelectTool('cursor_crosshair')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors relative",
          activeTool === 'cursor_crosshair' && "text-white bg-[#2a2e39]"
        )}
        title="Crosshair (Cursor)"
      >
        <Crosshair className="w-4 h-4" />
      </button>

      {/* 2. Lines & Rays */}
      <button
        onClick={() => onSelectTool('trendline')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          (activeTool === 'trendline' || activeTool === 'horizontal_line') && "text-white bg-[#2a2e39]"
        )}
        title="Trendline / Lines"
      >
        <TrendingUp className="w-4 h-4" />
      </button>

      {/* 3. Fibonacci Retracement */}
      <button
        onClick={() => onSelectTool('fib_retracement')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          activeTool === 'fib_retracement' && "text-white bg-[#2a2e39]"
        )}
        title="Fibonacci Retracement"
      >
        <SlidersHorizontal className="w-4 h-4" />
      </button>

      {/* 4. Geometric Shapes */}
      <button
        onClick={() => onSelectTool('rectangle')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          activeTool === 'rectangle' && "text-white bg-[#2a2e39]"
        )}
        title="Rectangle / Geometric Shapes"
      >
        <Square className="w-4 h-4" />
      </button>

      {/* 5. Annotation / Text */}
      <button
        onClick={() => onSelectTool('text')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          activeTool === 'text' && "text-white bg-[#2a2e39]"
        )}
        title="Text & Annotation"
      >
        <Type className="w-4 h-4" />
      </button>

      {/* 6. Patterns */}
      <button
        onClick={() => onSelectTool('head_and_shoulders')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          activeTool === 'head_and_shoulders' && "text-white bg-[#2a2e39]"
        )}
        title="Patterns (Head & Shoulders, Elliott)"
      >
        <Activity className="w-4 h-4" />
      </button>

      {/* 7. Prediction & Measure */}
      <button
        onClick={() => onSelectTool('price_range_ruler')}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          activeTool === 'price_range_ruler' && "text-white bg-[#2a2e39]"
        )}
        title="Price & Date Measurement Ruler"
      >
        <Ruler className="w-4 h-4" />
      </button>

      <div className="w-6 h-px bg-[#2a2e39] my-2" />

      {/* Magnet Mode */}
      <button
        onClick={onToggleMagnet}
        className={cn(
          "p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors",
          magnetMode !== 'off' && "text-[#2962ff] bg-[#2962ff]/10"
        )}
        title={`Magnet Mode: ${magnetMode.toUpperCase()}`}
      >
        <Magnet className="w-4 h-4" />
      </button>

      {/* Lock All Drawings */}
      <button
        className="p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors"
        title="Lock All Drawings"
      >
        <Lock className="w-4 h-4" />
      </button>

      {/* Hide All Drawings */}
      <button
        className="p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-white transition-colors"
        title="Hide All Drawings"
      >
        <Eye className="w-4 h-4" />
      </button>

      {/* Delete / Clear */}
      <button
        onClick={onClearAll}
        className="p-2 rounded hover:bg-[#2a2e39] text-[#787b86] hover:text-[#f23645] transition-colors"
        title="Delete All Drawings"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}
