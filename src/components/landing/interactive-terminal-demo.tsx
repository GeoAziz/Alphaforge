'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ShieldCheck, Target, ShieldAlert, ArrowUpRight, CheckCircle2, Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export function InteractiveTerminalDemo() {
  const [selectedAsset, setSelectedAsset] = useState<'BTC' | 'ETH' | 'SOL'>('BTC');

  const assets = {
    BTC: {
      ticker: 'BTC/USDT',
      direction: 'LONG',
      entry: 67420.00,
      target: 71200.00,
      stopLoss: 65800.00,
      confidence: 91,
      sharpe: 2.45,
      riskRatio: '1 : 2.33',
      notionalSize: '$2,000.00',
      maxModelLoss: '$48.06 (0.048% of total equity)',
      gateValidation: '6/6 Passed',
    },
    ETH: {
      ticker: 'ETH/USDT',
      direction: 'LONG',
      entry: 3480.00,
      target: 3720.00,
      stopLoss: 3390.00,
      confidence: 84,
      sharpe: 2.18,
      riskRatio: '1 : 2.67',
      notionalSize: '$2,000.00',
      maxModelLoss: '$51.72 (0.051% of total equity)',
      gateValidation: '6/6 Passed',
    },
    SOL: {
      ticker: 'SOL/USDT',
      direction: 'LONG',
      entry: 178.50,
      target: 198.00,
      stopLoss: 171.00,
      confidence: 88,
      sharpe: 2.62,
      riskRatio: '1 : 2.60',
      notionalSize: '$2,000.00',
      maxModelLoss: '$84.03 (0.084% of total equity)',
      gateValidation: '6/6 Passed',
    },
  };

  const current = assets[selectedAsset];

  return (
    <section id="terminal" className="py-24 border-t border-border/40 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary mb-2">
            <Play size={14} /> Interactive Simulation
          </div>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-foreground">
            Precision Execution Envelopes
          </h2>
          <p className="text-muted-foreground text-sm font-medium mt-3">
            Every AI signal is bounded by mathematically calculated profit targets and mandatory pre-trade stop loss constraints.
          </p>

          {/* Asset Selector */}
          <div className="flex justify-center gap-3 mt-8">
            {(['BTC', 'ETH', 'SOL'] as const).map((coin) => (
              <button
                key={coin}
                onClick={() => setSelectedAsset(coin)}
                className={cn(
                  "px-5 py-2 rounded-xl text-xs font-black font-mono uppercase tracking-wider transition-all",
                  selectedAsset === coin
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105"
                    : "border border-border/80 bg-surface/50 text-muted-foreground hover:text-foreground"
                )}
              >
                {coin}/USDT
              </button>
            ))}
          </div>
        </div>

        {/* Mock Terminal Card */}
        <div className="max-w-4xl mx-auto rounded-3xl border border-border/80 bg-surface/60 backdrop-blur-xl overflow-hidden shadow-2xl">
          {/* Terminal Window Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border/60 bg-surface/80">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red/80" />
              <div className="w-3 h-3 rounded-full bg-amber-400/80" />
              <div className="w-3 h-3 rounded-full bg-green/80" />
              <span className="ml-3 text-xs font-mono font-bold text-muted-foreground uppercase">
                AlphaForge Signal Execution Engine // {current.ticker}
              </span>
            </div>
            <Badge variant="outline" className="text-[10px] font-black uppercase tracking-wider text-green border-green/30 bg-green/10">
              {current.gateValidation}
            </Badge>
          </div>

          {/* Terminal Content */}
          <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Order Parameter</div>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-3xl font-black font-mono text-foreground">{current.ticker}</span>
                  <Badge className="bg-green text-green-foreground font-black text-xs uppercase px-2.5 py-0.5">
                    {current.direction}
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-2">
                <div className="p-3.5 rounded-xl border border-border/60 bg-background/50">
                  <div className="text-[9px] font-black uppercase tracking-wider text-muted-foreground">Target (TP)</div>
                  <div className="text-sm font-mono font-black text-green mt-1">${current.target.toLocaleString()}</div>
                </div>
                <div className="p-3.5 rounded-xl border border-border/60 bg-background/50">
                  <div className="text-[9px] font-black uppercase tracking-wider text-muted-foreground">Entry Price</div>
                  <div className="text-sm font-mono font-black text-foreground mt-1">${current.entry.toLocaleString()}</div>
                </div>
                <div className="p-3.5 rounded-xl border border-border/60 bg-background/50">
                  <div className="text-[9px] font-black uppercase tracking-wider text-muted-foreground">Stop Loss (SL)</div>
                  <div className="text-sm font-mono font-black text-red mt-1">${current.stopLoss.toLocaleString()}</div>
                </div>
              </div>

              {/* Reward/Risk Stats */}
              <div className="space-y-2 pt-2 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground">Ensemble Confidence:</span>
                  <span className="font-bold text-foreground">{current.confidence}%</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground">Historical Sharpe Ratio:</span>
                  <span className="font-bold text-foreground">{current.sharpe}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40">
                  <span className="text-muted-foreground">Risk/Reward Profile:</span>
                  <span className="font-bold text-primary">{current.riskRatio}</span>
                </div>
              </div>
            </div>

            {/* Risk Engine Guardrails Breakdown */}
            <div className="p-6 rounded-2xl border border-border/60 bg-background/40 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-foreground mb-4">
                  <ShieldCheck size={16} className="text-primary" /> Active Pre-Trade Guardrails
                </div>

                <div className="space-y-3.5 text-xs">
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 size={15} className="text-green shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-foreground">Position Size Cap (2.0%):</span>
                      <p className="text-muted-foreground text-[11px] mt-0.5 font-mono">Notional allocation capped at {current.notionalSize}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 size={15} className="text-green shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-foreground">Mandatory Bounded Loss:</span>
                      <p className="text-muted-foreground text-[11px] mt-0.5 font-mono">Theoretical loss at SL: {current.maxModelLoss}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 size={15} className="text-green shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-foreground">Global Leverage Cap:</span>
                      <p className="text-muted-foreground text-[11px] mt-0.5 font-mono">Order strictly bound by 5x platform ceiling</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-4 border-t border-border/40">
                <Link href="/dashboard" className="w-full">
                  <Button className="w-full h-11 uppercase text-xs font-black tracking-wider bg-primary hover:bg-primary/90 text-primary-foreground gap-1.5">
                    Open Full Terminal Execution View <ArrowUpRight size={14} />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
