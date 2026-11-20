'use client';

import React from 'react';
import { ChartInstrument, OHLCVBar } from '@/lib/charting/types';
import { cn } from '@/lib/utils';

interface InChartLegendProps {
  instrument: ChartInstrument;
  interval: string;
  currentBar: OHLCVBar | null;
  lastBar: OHLCVBar | null;
  rsiValue?: number;
}

export function InChartLegend({
  instrument,
  interval,
  currentBar,
  lastBar,
  rsiValue,
}: InChartLegendProps) {
  const bar = currentBar || lastBar;
  if (!bar) return null;

  const isUp = bar.close >= bar.open;
  const change = bar.close - bar.open;
  const changePct = ((change / bar.open) * 100).toFixed(2);

  return (
    <div className="absolute top-3 left-4 z-10 flex flex-col gap-1 select-none pointer-events-none text-xs font-mono">
      {/* Line 1: Title, Interval, Exchange, Status */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-bold text-white font-sans text-sm">{instrument.name}</span>
        <span className="text-[#787b86]">·</span>
        <span className="font-bold text-[#d1d4dc]">{interval}</span>
        <span className="text-[#787b86]">·</span>
        <span className="text-[#787b86]">{instrument.exchange}</span>

        {/* Provenance Badge */}
        <span className={cn(
          "text-[10px] px-1.5 py-0.2 rounded font-sans uppercase font-bold tracking-wider",
          instrument.feedClassification === 'live' && "bg-[#089981]/20 text-[#089981] border border-[#089981]/40",
          instrument.feedClassification === 'delayed_15m' && "bg-amber-400/20 text-amber-400 border border-amber-400/40",
          instrument.feedClassification === 'indicative' && "bg-[#2962ff]/20 text-[#2962ff] border border-[#2962ff]/40",
        )}>
          {instrument.feedClassification === 'live' ? '● Real-Time' : instrument.feedClassification === 'delayed_15m' ? '15m Delayed' : 'Indicative'}
        </span>
      </div>

      {/* Line 2: OHLCV Numerical Cursor Values */}
      <div className="flex items-center gap-3 text-[11px] text-[#787b86] flex-wrap">
        <div>
          <span>O </span>
          <span className={isUp ? "text-[#089981]" : "text-[#f23645]"}>{bar.open.toFixed(2)}</span>
        </div>
        <div>
          <span>H </span>
          <span className={isUp ? "text-[#089981]" : "text-[#f23645]"}>{bar.high.toFixed(2)}</span>
        </div>
        <div>
          <span>L </span>
          <span className={isUp ? "text-[#089981]" : "text-[#f23645]"}>{bar.low.toFixed(2)}</span>
        </div>
        <div>
          <span>C </span>
          <span className={isUp ? "text-[#089981]" : "text-[#f23645]"}>{bar.close.toFixed(2)}</span>
        </div>
        <div className={isUp ? "text-[#089981]" : "text-[#f23645]"}>
          <span>{change >= 0 ? `+${change.toFixed(2)}` : change.toFixed(2)} ({change >= 0 ? `+${changePct}` : changePct}%)</span>
        </div>
        <div>
          <span>Vol </span>
          <span className="text-white">{(bar.volume / 1000).toFixed(2)}K</span>
        </div>
        {rsiValue !== undefined && (
          <div className="text-[#b39ddb]">
            <span>RSI (14) </span>
            <span>{rsiValue.toFixed(2)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
