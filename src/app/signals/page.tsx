"use client";

import { useState } from "react";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { ConfidencePill } from "@/components/shared/confidence-pill";
import { mockSignals } from "@/data/mock-signals";
import { Signal } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronRight, Filter, Search, Clock, Target, TrendingUp } from "lucide-react";

export default function SignalsPage() {
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);

  return (
    <div className="flex h-full">
      <div className="flex-1 p-8 space-y-8 overflow-y-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-black tracking-tight uppercase">Signals Feed</h1>
            <p className="text-muted-foreground text-sm">Institutional grade algorithmic intelligence updated in real-time.</p>
          </div>
          
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0">
            {['All Assets', 'BTC', 'ETH', 'SOL', 'ALTS'].map((filter, i) => (
              <button 
                key={filter}
                className={cn(
                  "px-3 py-1.5 rounded-full text-[10px] font-bold uppercase transition-all whitespace-nowrap",
                  i === 0 ? "bg-primary text-primary-foreground" : "bg-elevated text-text-muted hover:text-text-primary"
                )}
              >
                {filter}
              </button>
            ))}
          </div>
        </header>

        <div className="grid grid-cols-1 gap-4">
          {mockSignals.map((signal) => (
            <SpotlightCard 
              key={signal.id} 
              className={cn(
                "p-6 cursor-pointer group transition-all",
                selectedSignal?.id === signal.id ? "border-primary/50 bg-primary/5" : ""
              )}
              onClick={() => setSelectedSignal(signal)}
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "px-3 py-1 rounded text-xs font-black uppercase tracking-widest",
                    signal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                  )}>
                    {signal.direction}
                  </div>
                  <div>
                    <div className="text-lg font-bold">{signal.asset}</div>
                    <div className="text-[10px] text-text-muted font-medium uppercase tracking-wider">{signal.strategy}</div>
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <div className="hidden md:block">
                    <div className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Entry Price</div>
                    <div className="text-sm font-mono font-bold">${signal.entryPrice.toLocaleString()}</div>
                  </div>
                  <div className="hidden md:block">
                    <div className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Risk/Reward</div>
                    <div className="text-sm font-mono font-bold text-primary">{signal.riskRewardRatio}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <ConfidencePill score={signal.confidence} />
                    <ChevronRight className={cn(
                      "text-text-muted transition-transform group-hover:translate-x-1",
                      selectedSignal?.id === signal.id && "rotate-90 md:rotate-0"
                    )} />
                  </div>
                </div>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </div>

      {/* Right Detail Panel */}
      {selectedSignal && (
        <aside className="hidden lg:block w-[400px] border-l border-border-subtle bg-surface p-8 overflow-y-auto space-y-8 animate-in slide-in-from-right duration-300">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black uppercase tracking-tighter">Signal Detail</h2>
            <button 
              onClick={() => setSelectedSignal(null)}
              className="text-text-muted hover:text-text-primary text-[10px] font-bold uppercase"
            >
              Close [ESC]
            </button>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-elevated/50 border border-border-subtle">
              <div className="flex items-center justify-between mb-4">
                <div className="text-2xl font-black">{selectedSignal.asset}</div>
                <div className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-black uppercase",
                  selectedSignal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                )}>
                  {selectedSignal.direction}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-surface border border-border-subtle">
                  <div className="text-[9px] text-text-muted font-black uppercase mb-1">Stop Loss</div>
                  <div className="text-sm font-mono font-bold text-red">${selectedSignal.stopLoss.toLocaleString()}</div>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border-subtle">
                  <div className="text-[9px] text-text-muted font-black uppercase mb-1">Take Profit</div>
                  <div className="text-sm font-mono font-bold text-green">${selectedSignal.takeProfit.toLocaleString()}</div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase text-text-muted tracking-widest">Confidence Drivers</h3>
              <div className="space-y-3">
                {selectedSignal.drivers.map((driver, i) => (
                  <div key={i} className="space-y-1.5">
                    <div className="flex justify-between text-[10px]">
                      <span className="font-medium">{driver.label}</span>
                      <span className="text-primary font-bold">{(driver.weight * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1 w-full bg-border-subtle rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${driver.weight * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 space-y-2">
              <div className="flex items-center gap-2 text-primary">
                <Target size={14} />
                <span className="text-[10px] font-black uppercase">Strategy Insight</span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                The {selectedSignal.strategy} strategy detected a high-probability liquidity sweep followed by an aggressive reversal. Institutional buy orders are clustering around the entry level.
              </p>
            </div>
          </div>

          <button className="w-full py-4 rounded-xl bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-90 transition-all">
            Execute Position
          </button>
        </aside>
      )}
    </div>
  );
}
