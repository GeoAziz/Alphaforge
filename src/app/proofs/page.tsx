'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Signal, SignalProof } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { ShieldCheck, Search, Filter, ArrowRight, Database, Fingerprint, ExternalLink, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export default function ProofCenterPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.signals.getLiveSignals('public').then(data => {
      setSignals(data);
      setIsLoading(false);
    });
  }, []);

  const filtered = signals.filter(s => s.asset.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="p-8 space-y-8 pb-32 max-w-7xl mx-auto animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Proof Center</h1>
        <p className="text-muted-foreground text-sm font-medium">Immutable verification logs for every signal issued by AlphaForge nodes.</p>
      </header>

      <div className="flex flex-col md:flex-row gap-4 bg-elevated/20 p-4 rounded-2xl border border-border-subtle sticky top-4 z-30 backdrop-blur-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input 
            placeholder="Search verified signals (Asset, ID, Hash)..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 h-12 bg-surface/50 border-border-subtle text-xs font-bold uppercase"
          />
        </div>
        <Button variant="outline" className="h-12 border-border-subtle uppercase text-[10px] font-black px-6 gap-2 hover:bg-elevated">
          <Filter size={14} /> Filter Registry
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {isLoading ? (
          Array(5).fill(0).map((_, i) => <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />)
        ) : filtered.map((signal) => (
          <SpotlightCard key={signal.id} className="p-6 group hover:border-primary/30 transition-all">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center gap-6">
                <div className="w-12 h-12 rounded-xl bg-green/10 flex items-center justify-center text-green border border-green/20">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-black tracking-tighter uppercase">{signal.asset}</span>
                    <Badge variant="outline" className="text-[8px] font-black uppercase border-green/20 text-green">Verified Proof</Badge>
                  </div>
                  <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest flex items-center gap-2 mt-1">
                    {signal.strategy}
                    <div className="w-1 h-1 rounded-full bg-border-subtle" />
                    Resolved: {new Date(signal.createdAt).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-8 text-right md:text-left">
                <div className="hidden md:block">
                  <div className="text-[9px] font-black text-text-muted uppercase mb-1">Audit Hash</div>
                  <div className="text-[10px] font-mono font-bold truncate w-32">0x7f8e...3a2b</div>
                </div>
                <div>
                  <div className="text-[9px] font-black text-text-muted uppercase mb-1">Verification Status</div>
                  <div className="text-[10px] font-black text-green uppercase tracking-widest">Immutable Log</div>
                </div>
                <div className="flex items-center justify-end">
                  <Link href={`/proofs/${signal.id}`}>
                    <Button variant="ghost" className="h-10 px-6 text-[10px] font-black uppercase text-primary hover:bg-primary/10 gap-2 group/btn">
                      Examine Proof <ArrowRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </SpotlightCard>
        ))}
      </div>

      <div className="p-8 rounded-3xl bg-primary/5 border border-primary/10 flex flex-col md:flex-row items-center justify-between gap-8 mt-12">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Database size={24} className="text-primary" />
            <h3 className="text-xl font-black uppercase tracking-tight">Institutional Transparency</h3>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed font-medium uppercase text-[10px]">AlphaForge uses SHA-256 anchoring to ensure that every historical signal is audit-verifiable and tamper-proof.</p>
        </div>
        <Button className="h-12 bg-primary text-primary-foreground font-black uppercase text-[10px] px-8 rounded-xl shrink-0">Review Cryptographic Node Protocol</Button>
      </div>
    </div>
  );
}
