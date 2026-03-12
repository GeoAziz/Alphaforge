'use client';

import { useEffect, useState } from 'react';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Bell, Zap, ShieldAlert, CheckCircle2 } from 'lucide-react';
// Firebase hooks removed in MVP mock mode:
// import { useCollection, useFirestore, useMemoFirebase, useUser } from '@/firebase';
// import { collection, query, orderBy, limit } from 'firebase/firestore';
import { Notification } from '@/lib/types';
import { cn } from '@/lib/utils';

const MOCK_ALERTS: Notification[] = [
  { id: 'a-1', userId: 'mock-user-001', type: 'signal', title: 'BTCUSDT Long Signal Triggered', message: 'Momentum Breakout node identified 92% confidence breakout on 4H cluster.', read: false, critical: false, createdAt: new Date().toISOString() },
  { id: 'a-2', userId: 'mock-user-001', type: 'trade', title: 'Position Established — SOLUSDT', message: 'Institutional LONG position confirmed at 142.30 node entry.', read: true, critical: false, createdAt: new Date(Date.now() - 3600000).toISOString() },
  { id: 'a-3', userId: 'mock-user-001', type: 'risk', title: 'Risk Threshold Advisory', message: 'Portfolio margin utilization reached 14.5%. Review cluster exposure.', read: false, critical: true, createdAt: new Date(Date.now() - 7200000).toISOString() },
];

export function QuickAlerts() {
  const [alerts, setAlerts] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock mode: simulate async load with mock data
    const t = setTimeout(() => {
      setAlerts(MOCK_ALERTS);
      setIsLoading(false);
    }, 300);
    return () => clearTimeout(t);
  }, []);

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