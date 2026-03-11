'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Strategy } from '@/lib/types';
import { Target, Activity, ShieldCheck, TrendingUp, BarChart, Zap, ShieldAlert, X, ChevronRight, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';

export default function StrategiesPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  const strategiesQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'strategies'), orderBy('winRate', 'desc'));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<Strategy>(strategiesQuery);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Strategies Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to browse proprietary algorithmic engines.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Core Strategies</h1>
        <p className="text-muted-foreground text-sm">Proprietary algorithmic engines driving AlphaForge intelligence.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {isLoading ? (
          Array(6).fill(0).map((_, i) => (
            <div key={i} className="h-64 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
          ))
        ) : strategies?.map((strategy) => (
          <SpotlightCard key={strategy.id} className="p-6 flex flex-col justify-between group cursor-pointer" onClick={() => setSelectedStrategy(strategy)}>
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                  <Target size={24} />
                </div>
                <div className="flex flex-col items-end gap-2">
                  <Badge className={cn(
                    "uppercase font-black text-[10px]",
                    strategy.isActive ? "bg-green/20 text-green" : "bg-red/20 text-red"
                  )}>
                    {strategy.isActive ? 'Active' : 'Offline'}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] uppercase font-black">{strategy.riskLevel} Risk</Badge>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-black tracking-tight">{strategy.name}</h3>
                <p className="text-xs text-text-muted leading-relaxed mt-1 line-clamp-2">{strategy.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border-subtle">
                <div>
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1 flex items-center gap-1">
                    <TrendingUp size={10} className="text-green" /> Win Rate
                  </div>
                  <div className="text-lg font-black font-mono text-green">{strategy.winRate}%</div>
                </div>
                <div>
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1 flex items-center gap-1">
                    <Zap size={10} className="text-primary" /> Avg ROI
                  </div>
                  <div className="text-lg font-black font-mono text-primary">+{strategy.avgRoi}%</div>
                </div>
              </div>
            </div>

            <Button className="w-full mt-6 bg-elevated hover:bg-primary border-border-subtle font-black uppercase text-[10px] h-10 gap-2">
              <BarChart size={14} /> View Deep Analytics
            </Button>
          </SpotlightCard>
        ))}
      </div>

      {/* Strategy Detail Sheet */}
      <Sheet open={!!selectedStrategy} onOpenChange={(open) => !open && setSelectedStrategy(null)}>
        <SheetContent className="glass sm:max-w-xl border-border-subtle p-0 overflow-hidden">
          {selectedStrategy && (
            <div className="h-full flex flex-col">
              <div className="p-8 space-y-8 flex-1 overflow-y-auto">
                <SheetHeader className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                      <Target size={28} />
                    </div>
                    <Badge className="bg-primary/20 text-primary border-primary/30 uppercase font-black text-xs h-8 px-4">Institutional Cluster</Badge>
                  </div>
                  <div className="space-y-1">
                    <SheetTitle className="text-3xl font-black uppercase tracking-tighter">{selectedStrategy.name}</SheetTitle>
                    <p className="text-xs text-text-muted font-bold uppercase tracking-widest">Node ID: {selectedStrategy.id}</p>
                  </div>
                </SheetHeader>

                <p className="text-sm text-text-secondary leading-relaxed font-medium">
                  {selectedStrategy.description}
                </p>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle space-y-1">
                    <div className="text-[9px] font-black text-text-muted uppercase">Efficiency</div>
                    <div className="text-lg font-black font-mono text-green">{selectedStrategy.winRate}%</div>
                  </div>
                  <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle space-y-1">
                    <div className="text-[9px] font-black text-text-muted uppercase">Sharpe</div>
                    <div className="text-lg font-black font-mono text-primary">{selectedStrategy.sharpeRatio}</div>
                  </div>
                  <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle space-y-1">
                    <div className="text-[9px] font-black text-text-muted uppercase">Profit Factor</div>
                    <div className="text-lg font-black font-mono text-accent">{selectedStrategy.profitFactor}</div>
                  </div>
                  <div className="p-4 rounded-xl bg-elevated/30 border border-border-subtle space-y-1">
                    <div className="text-[9px] font-black text-text-muted uppercase">Drawdown</div>
                    <div className="text-lg font-black font-mono text-red">{selectedStrategy.maxDrawdown}%</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-[10px] font-black uppercase tracking-widest text-text-muted flex items-center gap-2">
                    <Info size={14} className="text-primary" /> Algorithmic Logic
                  </h3>
                  <div className="p-6 rounded-2xl bg-surface border border-dashed border-border-subtle space-y-4">
                    <div className="flex items-start gap-3">
                      <ChevronRight size={14} className="text-primary mt-1" />
                      <p className="text-xs font-bold uppercase leading-relaxed text-text-secondary">Momentum identification via cross-exchange volume clusters and order-book depth analysis.</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <ChevronRight size={14} className="text-primary mt-1" />
                      <p className="text-xs font-bold uppercase leading-relaxed text-text-secondary">Automated risk-parity sizing calibrated to institutional 2.5% max exposure limits.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-8 bg-elevated/20 border-t border-border-subtle flex gap-4">
                <Button className="flex-1 h-14 bg-primary text-primary-foreground font-black uppercase text-xs rounded-xl shadow-lg">Activate Execution Node</Button>
                <Button variant="ghost" className="h-14 font-black uppercase text-xs px-8" onClick={() => setSelectedStrategy(null)}>Close</Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
