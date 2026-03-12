'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { useCollection, useFirestore, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, limit } from 'firebase/firestore';
import { Signal } from '@/lib/types';
import { History } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * RecentSignals - Chronological resolution ledger for the bento grid.
 */
export function RecentSignals() {
  const { user } = useUser();
  const db = useFirestore();

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'signals'), orderBy('createdAt', 'desc'), limit(5));
  }, [db, user]);

  const { data: signals, isLoading } = useCollection<Signal>(signalsQuery);

  return (
    <SpotlightCard className="p-8 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <History size={16} className="text-text-muted" />
          Recent Resolutions
        </h3>
        <span className="text-[9px] font-black uppercase text-text-muted tracking-tighter">Node AF-US-01</span>
      </div>

      <div className="space-y-2 flex-1">
        {isLoading ? (
          Array(5).fill(0).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))
        ) : !signals || signals.length === 0 ? (
          <div className="h-full flex items-center justify-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
            Scanning signal history...
          </div>
        ) : signals.map((signal) => (
          <div key={signal.id} className="p-3 rounded-lg border border-transparent hover:border-border-subtle hover:bg-elevated/10 transition-all flex items-center justify-between group">
            <div className="flex items-center gap-3">
              <div className={cn(
                "text-[10px] font-black uppercase tracking-widest",
                signal.direction === 'LONG' ? "text-green" : "text-red"
              )}>
                {signal.direction[0]}
              </div>
              <div className="font-black text-xs uppercase tracking-tight text-text-secondary group-hover:text-text-primary transition-colors">{signal.asset}</div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-[10px] font-mono font-bold text-text-muted uppercase hidden sm:block">{signal.strategy}</div>
              <div className="flex items-center gap-2 min-w-[60px] justify-end">
                {signal.pnlPercent !== undefined && signal.pnlPercent !== null ? (
                  <div className={cn(
                    "text-[10px] font-black font-mono",
                    signal.pnlPercent >= 0 ? "text-green" : "text-red"
                  )}>
                    {signal.pnlPercent > 0 ? '+' : ''}{signal.pnlPercent}%
                  </div>
                ) : (
                  <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" title="Active" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
