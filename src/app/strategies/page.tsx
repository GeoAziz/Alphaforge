'use client';

import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Strategy } from '@/lib/types';
import { Target, Activity, ShieldCheck, TrendingUp, BarChart, Zap, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function StrategiesPage() {
  const { user } = useUser();
  const db = useFirestore();

  const strategiesQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    // Fix: Access user-specific strategies subcollection to comply with security rules
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
          <p className="text-sm text-text-muted">Please connect your session to browse proprietary algorithmic engines driving AlphaForge intelligence.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
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
          <SpotlightCard key={strategy.id} className="p-6 flex flex-col justify-between group">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                  <Target size={24} />
                </div>
                <div className="flex flex-col items-end gap-2">
                  <Badge className={cn(
                    "uppercase font-black text-[10px]",
                    strategy.isActive ? "bg-green/20 text-green border-green/30" : "bg-red/20 text-red border-red/30"
                  )}>
                    {strategy.isActive ? 'Active' : 'Offline'}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] uppercase font-black">
                    {strategy.riskLevel} Risk
                  </Badge>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-black tracking-tight">{strategy.name}</h3>
                <p className="text-xs text-text-muted leading-relaxed mt-1 line-clamp-2">
                  {strategy.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border-subtle">
                <div>
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-1 flex items-center gap-1">
                    <TrendingUp size={10} /> Win Rate
                  </div>
                  <div className="text-lg font-black font-mono text-green">{strategy.winRate}%</div>
                </div>
                <div>
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-1 flex items-center gap-1">
                    <Zap size={10} /> Avg ROI
                  </div>
                  <div className="text-lg font-black font-mono text-primary">+{strategy.avgRoi}%</div>
                </div>
                <div>
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-1 flex items-center gap-1">
                    <Activity size={10} /> Sharpe
                  </div>
                  <div className="text-sm font-black font-mono">{strategy.sharpeRatio}</div>
                </div>
                <div>
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-1 flex items-center gap-1">
                    <ShieldCheck size={10} /> Drawdown
                  </div>
                  <div className="text-sm font-black font-mono text-red">{strategy.maxDrawdown}%</div>
                </div>
              </div>
            </div>

            <Button className="w-full mt-6 bg-elevated hover:bg-primary hover:text-primary-foreground border border-border-subtle font-black uppercase text-xs h-10 gap-2">
              <BarChart size={14} />
              View Deep Analytics
            </Button>
          </SpotlightCard>
        ))}
      </div>
    </div>
  );
}
