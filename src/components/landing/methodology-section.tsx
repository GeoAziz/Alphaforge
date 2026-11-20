'use client';

import { ShieldCheck, Cpu, Database, Fingerprint, Layers, BarChart, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function MethodologySection() {
  const steps = [
    {
      num: '01',
      title: 'Multi-Source Tick Ingestion',
      desc: 'Real-time orderbook and trade data streaming continuously from Binance, Bybit, OKX, and CoinGecko liquidity venues.',
      icon: Database,
    },
    {
      num: '02',
      title: 'Quantitative Feature Engine',
      desc: 'Automated extraction of order flow imbalance, realized volatility, and momentum regimes across 50+ financial indicators.',
      icon: Layers,
    },
    {
      num: '03',
      title: 'Ensemble ML Scoring',
      desc: 'Gradient Boosting and Random Forest models evaluate probabilities with cross-validated overfitting prevention.',
      icon: Cpu,
    },
    {
      num: '04',
      title: 'Cryptographic Proof Anchoring',
      desc: 'Signal parameters, ML weights, and timestamps are hashed into an immutable, tamper-evident SHA-256 audit chain.',
      icon: Fingerprint,
    },
  ];

  return (
    <section id="methodology" className="py-24 border-t border-border/40 bg-surface/20 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="max-w-3xl mb-16">
          <div className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary mb-2">
            <Cpu size={14} /> Systematic Architecture
          </div>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-foreground">
            The Quantitative Alpha Pipeline
          </h2>
          <p className="text-muted-foreground text-sm font-medium mt-3 leading-relaxed">
            Inspired by institutional hedge fund architectures (Renaissance Technologies, Citadel). Every published trade recommendation follows a deterministic, backtested pipeline.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="p-8 rounded-3xl border border-border/60 bg-surface/50 hover:bg-surface/80 hover:border-primary/40 transition-all duration-300 flex flex-col justify-between group shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-3xl font-black font-mono text-primary/40 group-hover:text-primary transition-colors">
                      {step.num}
                    </span>
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                      <Icon size={18} />
                    </div>
                  </div>

                  <h3 className="text-lg font-black text-foreground uppercase tracking-tight">{step.title}</h3>
                  <p className="text-muted-foreground text-xs font-medium leading-relaxed mt-3">{step.desc}</p>
                </div>

                <div className="mt-8 pt-4 border-t border-border/40 flex items-center text-[10px] font-black uppercase tracking-wider text-primary">
                  <span>Phase {step.num} Complete</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Public Proof Registry Callout */}
        <div className="mt-12 p-8 rounded-3xl border border-border/80 bg-gradient-to-r from-surface/80 via-surface/50 to-primary/5 flex flex-col md:flex-row items-center justify-between gap-6 backdrop-blur-md">
          <div className="space-y-1 text-center md:text-left">
            <h4 className="text-lg font-black uppercase tracking-tight text-foreground flex items-center gap-2 justify-center md:justify-start">
              <Fingerprint size={20} className="text-accent" /> Public Hash-Chain Verification Registry
            </h4>
            <p className="text-muted-foreground text-xs font-medium max-w-xl">
              Inspect cryptographic proof logs for any signal issued by AlphaForge nodes. Independently verify SHA-256 mathematical hashes without an account.
            </p>
          </div>

          <Link href="/proofs">
            <Button size="lg" className="h-12 px-6 text-xs uppercase font-black tracking-wider bg-accent hover:bg-accent/90 text-accent-foreground shadow-lg shadow-accent/20 gap-2 shrink-0">
              Explore Proof Registry <ArrowRight size={14} />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
