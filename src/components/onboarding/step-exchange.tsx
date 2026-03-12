'use client';

import { Globe, ShieldCheck, Lock, Info } from "lucide-react";
import { cn } from "@/lib/utils";

const EXCHANGES = [
  { id: 'binance', name: 'Binance Institutional', logo: 'B' },
  { id: 'bybit', name: 'Bybit Perps Core', logo: 'BY' },
  { id: 'okx', name: 'OKX Alpha Node', logo: 'O' },
  { id: 'kraken', name: 'Kraken Trading', logo: 'K' },
];

export function StepExchange() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 mb-6">
          <Globe size={24} />
        </div>
        <h2 className="text-2xl font-black uppercase tracking-tight">Exchange Calibration</h2>
        <p className="text-sm text-text-muted leading-relaxed">
          Establish an institutional bridge to your liquidity clusters. AlphaForge uses high-frequency handshake protocols for execution parity.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {EXCHANGES.map((ex) => (
          <div key={ex.id} className="p-4 rounded-xl border border-border-subtle bg-elevated/20 hover:border-primary/30 transition-all cursor-pointer group">
            <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center font-black text-[10px] text-text-muted mb-3 group-hover:text-primary transition-colors">{ex.logo}</div>
            <div className="text-[10px] font-black uppercase tracking-tight">{ex.name}</div>
          </div>
        ))}
      </div>

      <div className="space-y-4 pt-4">
        <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle space-y-3">
          <div className="flex items-center gap-2 text-primary">
            <Lock size={14} />
            <span className="text-[10px] font-black uppercase tracking-widest">Idempotent Handshake Node</span>
          </div>
          <p className="text-[10px] font-bold text-text-secondary leading-relaxed uppercase">
            AlphaForge assigns a unique deterministic ID to every node trigger. If a connection jitter occurs, the risk engine ensures your trade is never executed twice.
          </p>
        </div>

        <div className="flex gap-3 items-center px-2">
          <Info size={14} className="text-text-muted" />
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest italic">Simulation mode enabled by default. No real capital required for initialization.</span>
        </div>
      </div>
    </div>
  );
}
