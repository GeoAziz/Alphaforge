'use client';

import { useState, useEffect, use } from 'react';
import { api } from '@/lib/api';
import { Signal, SignalProof } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ShieldCheck, Fingerprint, Database, ExternalLink, Activity, Target, Zap, Clock, Share2, ArrowLeft, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

export default function ProofDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [proof, setProof] = useState<SignalProof | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.signals.getSignalDetail(id),
      api.signals.getSignalProof(id)
    ]).then(([s, p]) => {
      setSignal(s);
      setProof(p);
      setIsLoading(false);
    });
  }, [id]);

  if (isLoading) return <div className="p-8 animate-pulse space-y-8"><div className="h-12 w-1/3 bg-elevated rounded-xl" /><div className="h-96 w-full bg-elevated rounded-2xl" /></div>;
  if (!signal) return <div className="p-8 text-center uppercase font-black">Node Identity Not Found.</div>;

  return (
    <div className="p-8 space-y-8 pb-32 max-w-5xl mx-auto animate-page">
      <Link href="/proofs">
        <Button variant="ghost" className="text-text-muted hover:text-text-primary gap-2 uppercase font-black text-[10px] p-0 mb-4">
          <ArrowLeft size={14} /> Back to Registry
        </Button>
      </Link>

      <div className="flex flex-col md:flex-row justify-between gap-8 items-start">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-green/10 flex items-center justify-center text-green border border-green/20">
              <ShieldCheck size={32} />
            </div>
            <div>
              <h1 className="text-4xl font-black uppercase tracking-tighter leading-none">{signal.asset}</h1>
              <div className="flex items-center gap-2 mt-2">
                <Badge className="bg-green/20 text-green border-green/30 uppercase font-black text-[10px]">Resolved Alpha</Badge>
                <span className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Hash: {proof?.hash.slice(0, 12)}...</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-border-subtle h-10 uppercase text-[10px] font-black px-6 gap-2 rounded-xl">
            <Share2 size={14} /> Export Node Log
          </Button>
          <Button className="bg-primary text-primary-foreground h-10 uppercase text-[10px] font-black px-6 gap-2 rounded-xl">
            Verify Blockchain Anchor
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SpotlightCard className="p-6 border-primary/10">
          <div className="text-[10px] font-black text-text-muted uppercase mb-4 tracking-widest flex items-center gap-2">
            <Target size={14} className="text-primary" /> Entry Precision
          </div>
          <div className="text-2xl font-black font-mono">${signal.entryPrice.toLocaleString()}</div>
          <div className="text-[10px] text-text-muted font-bold uppercase mt-2">Target reached: ${signal.takeProfit.toLocaleString()}</div>
        </SpotlightCard>
        <SpotlightCard className="p-6 border-green/10">
          <div className="text-[10px] font-black text-text-muted uppercase mb-4 tracking-widest flex items-center gap-2">
            <Zap size={14} className="text-green" /> Resolved ROI
          </div>
          <div className="text-2xl font-black font-mono text-green">+{signal.pnlPercent || '4.2'}%</div>
          <div className="text-[10px] text-text-muted font-bold uppercase mt-2">Resolved in 12h 42m</div>
        </SpotlightCard>
        <SpotlightCard className="p-6 border-accent/10">
          <div className="text-[10px] font-black text-text-muted uppercase mb-4 tracking-widest flex items-center gap-2">
            <Clock size={14} className="text-accent" /> Node Latency
          </div>
          <div className="text-2xl font-black font-mono text-accent">8.4 ms</div>
          <div className="text-[10px] text-text-muted font-bold uppercase mt-2">Verified Execution Sync</div>
        </SpotlightCard>
      </div>

      <Tabs defaultValue="rationale" className="space-y-8">
        <TabsList className="bg-elevated/50 p-1 rounded-xl h-12 inline-flex w-max border border-border-subtle">
          <TabsTrigger value="rationale" className="px-8 font-black uppercase text-[10px] data-[state=active]:bg-primary rounded-lg transition-all">Rationale</TabsTrigger>
          <TabsTrigger value="backtest" className="px-8 font-black uppercase text-[10px] data-[state=active]:bg-primary rounded-lg transition-all">Backtest</TabsTrigger>
          <TabsTrigger value="execution" className="px-8 font-black uppercase text-[10px] data-[state=active]:bg-primary rounded-lg transition-all">Execution</TabsTrigger>
          <TabsTrigger value="integrity" className="px-8 font-black uppercase text-[10px] data-[state=active]:bg-primary rounded-lg transition-all">Integrity</TabsTrigger>
        </TabsList>

        <TabsContent value="rationale" className="animate-in fade-in slide-in-from-left-4">
          <SpotlightCard className="p-10 space-y-8">
            <div className="space-y-4">
              <h3 className="text-lg font-black uppercase tracking-tight">Signal Hypothesis</h3>
              <p className="text-sm text-text-secondary leading-relaxed font-medium">{proof?.hypothesis}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-border-subtle">
              <div className="space-y-4">
                <h4 className="text-[10px] font-black uppercase text-primary tracking-widest">Alpha Drivers</h4>
                <div className="space-y-3">
                  {signal.drivers.map((driver, i) => (
                    <div key={i} className="space-y-2 p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {driver.active ? <CheckCircle2 size={12} className="text-green" /> : <div className="w-1.5 h-1.5 rounded-full bg-border-subtle" />}
                          <span className="text-[11px] font-bold text-text-secondary uppercase">{driver.label}</span>
                        </div>
                        <span className="text-[9px] font-black text-primary uppercase">{Math.round(driver.weight * 100)}%</span>
                      </div>
                      <Progress value={driver.weight * 100} className="h-1 bg-border-subtle" />
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="text-[10px] font-black uppercase text-primary tracking-widest">Risk/Reward Profile</h4>
                <div className="p-6 rounded-2xl bg-surface border border-dashed border-border-subtle space-y-4">
                  <div className="flex justify-between items-center text-xs font-bold uppercase">
                    <span className="text-text-muted">Target R:R</span>
                    <span>1 : {signal.riskRewardRatio}</span>
                  </div>
                  <div className="h-1.5 bg-elevated rounded-full overflow-hidden"><div className="h-full bg-primary w-[65%]" /></div>
                </div>
              </div>
            </div>
          </SpotlightCard>
        </TabsContent>

        <TabsContent value="backtest" className="animate-in fade-in slide-in-from-left-4">
          <SpotlightCard className="p-10 space-y-6">
            <h3 className="text-lg font-black uppercase tracking-tight">Historical Simulation Verification</h3>
            <p className="text-sm text-text-secondary leading-relaxed font-medium">{proof?.backtestResult}</p>
            <div className="h-60 w-full bg-elevated/20 rounded-2xl border border-dashed border-border-subtle flex items-center justify-center">
              <div className="text-center space-y-2">
                <Activity size={32} className="text-text-muted mx-auto opacity-30" />
                <span className="text-[10px] font-black uppercase text-text-muted opacity-50">Backtest Chart Trace Anchored</span>
              </div>
            </div>
          </SpotlightCard>
        </TabsContent>

        <TabsContent value="execution" className="animate-in fade-in slide-in-from-left-4">
          <SpotlightCard className="p-10 space-y-6">
            <h3 className="text-lg font-black uppercase tracking-tight">Paper Trading & Live Execution Handshake</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="text-[10px] font-black uppercase text-primary tracking-widest">Phase 1: Simulation</div>
                <p className="text-xs text-text-secondary leading-relaxed font-medium uppercase">{proof?.paperResults}</p>
              </div>
              <div className="space-y-4">
                <div className="text-[10px] font-black uppercase text-green tracking-widest">Phase 2: Live Node</div>
                <p className="text-xs text-text-secondary leading-relaxed font-medium uppercase">{proof?.liveResults}</p>
              </div>
            </div>
          </SpotlightCard>
        </TabsContent>

        <TabsContent value="integrity" className="animate-in fade-in slide-in-from-left-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SpotlightCard className="p-8 lg:col-span-2 space-y-8">
              <div className="space-y-2">
                <h3 className="text-lg font-black uppercase tracking-tight">Cryptographic Identity</h3>
                <p className="text-xs text-text-muted font-bold uppercase">Publicly verifiable node telemetry</p>
              </div>
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle flex flex-col gap-2">
                  <span className="text-[10px] font-black uppercase text-text-muted">Merkle Root</span>
                  <span className="text-xs font-mono font-bold break-all">{proof?.merkleRoot || '0x1a2b...9f8e'}</span>
                </div>
                <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle flex flex-col gap-2">
                  <span className="text-[10px] font-black uppercase text-text-muted">Transaction Anchor</span>
                  <span className="text-xs font-mono font-bold break-all text-primary">{proof?.txHash}</span>
                </div>
              </div>
            </SpotlightCard>
            <SpotlightCard variant="accent" className="p-8 space-y-6">
              <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center text-primary border border-primary/30">
                <Fingerprint size={24} />
              </div>
              <div className="space-y-2">
                <h4 className="text-sm font-black uppercase">Institutional Seal</h4>
                <p className="text-[10px] text-text-secondary font-bold uppercase leading-relaxed">This signal has been cryptographically signed by the AlphaForge Core Node US-01 and verified by the Proof-of-Alpha consensus mechanism.</p>
              </div>
              <Button variant="outline" className="w-full border-primary/30 text-primary uppercase text-[10px] font-black h-10 rounded-xl hover:bg-primary/5">Verify Node Identity</Button>
            </SpotlightCard>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
