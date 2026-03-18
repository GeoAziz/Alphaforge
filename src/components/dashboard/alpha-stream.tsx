
'use client';

import { useEffect, useState } from 'react';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { useCollection, useFirestore, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, limit } from 'firebase/firestore';
import { api } from '@/lib/api';
import { Signal } from '@/lib/types';
import { Zap, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';

export function AlphaStream() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.signals.getLiveSignals('mock-user-001').then(data => {
      setSignals(data.slice(0, 4));
      setIsLoading(false);
    });
  }, []);

  return (
    <SpotlightCard className="p-8 h-full">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <Zap size={16} className="text-accent" />
          Alpha Stream
        </h3>
        <Link href="/signals" className="text-[10px] font-black uppercase text-accent hover:underline flex items-center gap-1">
          Full Stream <ChevronRight size={10} />
        </Link>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))
        ) : signals?.length === 0 ? (
          <div className="py-12 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
            Scanning signal frequencies...
          </div>
        ) : signals?.map((signal) => (
          <div key={signal.id} className="p-4 rounded-xl border border-border-subtle bg-elevated/10 group hover:border-accent/30 transition-all flex items-center justify-between cursor-pointer">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-black tracking-tight text-text-primary">{signal.asset}</span>
                <span className={cn(
                  "px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-widest",
                  signal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                )}>
                  {signal.direction}
                </span>
              </div>
              <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest">{signal.strategy}</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-black text-accent">{signal.confidence}%</div>
              <div className="text-[8px] font-black uppercase text-text-muted">Confidence</div>
            </div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
