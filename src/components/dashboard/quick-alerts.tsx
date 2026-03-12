'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Bell, Zap, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useCollection, useFirestore, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, limit } from 'firebase/firestore';
import { Notification } from '@/lib/types';
import { cn } from '@/lib/utils';

export function QuickAlerts() {
  const { user } = useUser();
  const db = useFirestore();

  const alertsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'notifications'), orderBy('createdAt', 'desc'), limit(3));
  }, [db, user]);

  const { data: alerts, isLoading } = useCollection<Notification>(alertsQuery);

  return (
    <SpotlightCard className="p-8 h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <Bell size={16} className="text-amber" />
          Terminal Node Feed
        </h3>
        <span className="text-[9px] font-black uppercase text-text-muted">Live Telemetry</span>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="h-14 w-full rounded-xl bg-elevated/20 animate-pulse" />
          ))
        ) : alerts?.length === 0 ? (
          <div className="py-8 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
            Monitoring frequency...
          </div>
        ) : alerts?.map((alert) => (
          <div key={alert.id} className="p-3 rounded-xl bg-elevated/10 border border-border-subtle flex items-start gap-3 hover:bg-elevated/20 transition-colors">
            <div className={cn(
              "mt-1 w-6 h-6 rounded-lg flex items-center justify-center shrink-0",
              alert.type === 'signal' ? "bg-primary/10 text-primary" : 
              alert.type === 'risk' ? "bg-red/10 text-red" : "bg-green/10 text-green"
            )}>
              {alert.type === 'signal' ? <Zap size={12} /> : 
               alert.type === 'risk' ? <ShieldAlert size={12} /> : <CheckCircle2 size={12} />}
            </div>
            <div className="space-y-0.5 overflow-hidden">
              <div className="text-[11px] font-black uppercase truncate text-text-primary">{alert.title}</div>
              <div className="text-[9px] text-text-muted font-bold truncate">{alert.message}</div>
            </div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}