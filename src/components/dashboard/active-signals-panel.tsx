'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { useCollection, useFirestore, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, limit, where } from 'firebase/firestore';
import { Signal } from '@/lib/types';
import { Zap, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';

/**
 * ActiveSignalsPanel - Compact bento cell for real-time high-priority nodes.
 */
export function ActiveSignalsPanel() {
  const { user } = useUser();
  const db = useFirestore();

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(
      collection(db, 'users', user.uid, 'signals'), 
      where('status', '==', 'active'),
      orderBy('createdAt', 'desc'), 
      limit(3)
    );
  }, [db, user]);

  const { data: signals, isLoading } = useCollection<Signal>(signalsQuery);

  return (
    <SpotlightCard className="p-8 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <Zap size={16} className="text-primary" />
          Active High-Signal
        </h3>
        <Link href="/signals" className="text-[10px] font-black uppercase text-primary hover:underline flex items-center gap-1">
          Full Stream <ChevronRight size={10} />
        </Link>
      </div>

      <div className="space-y-4 flex-1">
        {isLoading ? (
          Array(3).fill(0).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))
        ) : !signals || signals.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center py-12 text-center space-y-2 opacity-40 grayscale">
            <Zap size={32} className="text-text-muted" />
            <div className="text-[9px] font-black uppercase text-text-muted tracking-widest">Scanning frequency...</div>
          </div>
        ) : signals.map((signal) => (
          <Link key={signal.id} href="/signals" className="block p-4 rounded-xl border border-border-subtle bg-elevated/10 group hover:border-primary/30 transition-all flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={cn(
                "w-1 h-8 rounded-full",
                signal.direction === 'LONG' ? "bg-green" : "bg-red"
              )} />
              <div>
                <div className="font-black tracking-tight text-sm text-text-primary uppercase">{signal.asset}</div>
                <div className="text-[8px] text-text-muted font-bold uppercase tracking-widest">{signal.strategy}</div>
              </div>
            </div>
            <div className="text-right">
              <div className={cn(
                "text-sm font-black font-mono",
                signal.confidence >= 80 ? "text-green" : signal.confidence >= 60 ? "text-amber" : "text-red"
              )}>
                {signal.confidence}%
              </div>
              <div className="text-[8px] font-black uppercase text-text-muted">Confidence</div>
            </div>
          </Link>
        ))}
      </div>
    </SpotlightCard>
  );
}
