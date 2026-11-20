'use client';

import React, { useState } from 'react';
import { ArrowUp, ArrowDown, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickExecutionWidgetProps {
  symbol: string;
  bidPrice: number;
  askPrice: number;
  onTradeExecuted?: (side: 'BUY' | 'SELL', price: number, qty: number) => void;
}

export function QuickExecutionWidget({
  symbol,
  bidPrice,
  askPrice,
  onTradeExecuted,
}: QuickExecutionWidgetProps) {
  const [submitting, setSubmitting] = useState<'BUY' | 'SELL' | null>(null);
  const spread = Math.max(0.01, askPrice - bidPrice).toFixed(2);

  const handleExecute = (side: 'BUY' | 'SELL') => {
    setSubmitting(side);
    const targetPrice = side === 'BUY' ? askPrice : bidPrice;

    // Simulate backend PaperTradingEngine roundtrip (Architecture §10.1)
    setTimeout(() => {
      setSubmitting(null);
      if (onTradeExecuted) {
        onTradeExecuted(side, targetPrice, 1);
      }
    }, 400);
  };

  return (
    <div className="absolute top-16 left-4 z-10 flex items-center bg-[#1e222d]/90 backdrop-blur border border-[#2a2e39] rounded-lg shadow-2xl p-1 select-none">
      {/* SELL BUTTON */}
      <button
        onClick={() => handleExecute('SELL')}
        disabled={submitting !== null}
        className={cn(
          "flex flex-col items-center px-3 py-1 rounded transition-colors text-left",
          "hover:bg-[#f23645]/20 text-[#f23645] cursor-pointer"
        )}
      >
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#787b86]">SELL</span>
        <span className="font-mono font-bold text-xs text-white">
          {submitting === 'SELL' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : bidPrice.toFixed(2)}
        </span>
      </button>

      {/* SPREAD INDICATOR */}
      <div className="flex flex-col items-center px-2 text-[#787b86]">
        <span className="text-[9px] uppercase font-mono">Spread</span>
        <span className="text-[10px] font-mono font-semibold text-[#d1d4dc]">{spread}</span>
      </div>

      {/* BUY BUTTON */}
      <button
        onClick={() => handleExecute('BUY')}
        disabled={submitting !== null}
        className={cn(
          "flex flex-col items-center px-3 py-1 rounded transition-colors text-right",
          "hover:bg-[#089981]/20 text-[#089981] cursor-pointer"
        )}
      >
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#787b86]">BUY</span>
        <span className="font-mono font-bold text-xs text-white">
          {submitting === 'BUY' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : askPrice.toFixed(2)}
        </span>
      </button>
    </div>
  );
}
