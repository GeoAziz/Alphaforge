"use client";

import { useState, useEffect, useMemo } from "react";
import { useFirestore, useUser, useCollection, useMemoFirebase } from "@/firebase";
import { collection, query, orderBy } from "firebase/firestore";
import { addDocumentNonBlocking } from "@/firebase/non-blocking-updates";
import { SignalCard } from "@/components/signals/signal-card";
import { SignalFilters } from "@/components/signals/signal-filters";
import { SignalDetailPanel } from "@/components/signals/signal-detail-panel";
import { Signal, Position, Notification } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ShieldAlert, Activity } from "lucide-react";
import { SpotlightCard } from "@/components/shared/spotlight-card";

export default function SignalsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Filter States
  const [search, setSearch] = useState("");
  const [strategy, setStrategy] = useState("all");
  const [status, setStatus] = useState("active");
  const [confidence, setConfidence] = useState(0);

  useEffect(() => setMounted(true), []);

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, "users", user.uid, "signals"), orderBy("createdAt", "desc"));
  }, [db, user]);

  const { data: rawSignals, isLoading } = useCollection<Signal>(signalsQuery);

  const filteredSignals = useMemo(() => {
    if (!rawSignals) return [];
    return rawSignals.filter(s => {
      const matchesSearch = s.asset.toLowerCase().includes(search.toLowerCase());
      const matchesStrategy = strategy === "all" || s.strategy === strategy;
      const matchesStatus = status === "all" || s.status === status;
      const matchesConfidence = s.confidence >= confidence;
      return matchesSearch && matchesStrategy && matchesStatus && matchesConfidence;
    });
  }, [rawSignals, search, strategy, status, confidence]);

  function handleExecuteSignal(signal: Signal) {
    if (!user || !db) return;
    setIsExecuting(true);

    const positionsRef = collection(db, "users", user.uid, "positions");
    const notificationsRef = collection(db, "users", user.uid, "notifications");

    const newPosition: Partial<Position> = {
      asset: signal.asset,
      direction: signal.direction,
      entryPrice: signal.entryPrice,
      currentPrice: signal.entryPrice,
      quantity: 1,
      unrealizedPnl: 0,
      unrealizedPnlPercent: 0,
      riskExposure: 2.5,
      signalId: signal.id,
      openedAt: new Date().toISOString(),
    };

    const newNotification: Partial<Notification> = {
      type: 'trade',
      userId: user.uid,
      title: 'Position Established',
      message: `Institutional ${signal.direction} position established for ${signal.asset} via ${signal.strategy} node.`,
      read: false,
      critical: false,
      createdAt: new Date().toISOString(),
    };

    addDocumentNonBlocking(positionsRef, newPosition);
    addDocumentNonBlocking(notificationsRef, newNotification);

    setTimeout(() => {
      setIsExecuting(false);
      setSelectedSignal(null);
    }, 1500);
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Handshake Required</h2>
          <p className="text-sm text-text-muted leading-relaxed">Please connect your terminal session to authorize access to institutional data streams.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex h-full relative overflow-hidden animate-page",
      !mounted && "opacity-0"
    )}>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-8 space-y-8 pb-24 md:pb-8">
          <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-1">
              <h1 className="text-3xl font-black tracking-tighter uppercase leading-none">Intelligence Stream</h1>
              <p className="text-muted-foreground text-sm font-medium">Real-time algorithmic consensus and institutional signal rationale.</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-9 px-4 rounded-md border border-border-subtle bg-elevated/20 flex items-center gap-2 text-[10px] font-black uppercase text-green">
                <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
                Live Stream Active
              </div>
            </div>
          </header>

          <SignalFilters 
            search={search} onSearchChange={setSearch}
            strategy={strategy} onStrategyChange={setStrategy}
            status={status} onStatusChange={setStatus}
            confidence={confidence} onConfidenceChange={setConfidence}
            onClear={() => {
              setSearch("");
              setStrategy("all");
              setStatus("active");
              setConfidence(0);
            }}
          />

          <div className="space-y-4">
            {isLoading ? (
              Array(5).fill(0).map((_, i) => (
                <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
              ))
            ) : filteredSignals.length === 0 ? (
              <div className="py-20 text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-elevated mx-auto flex items-center justify-center text-text-muted">
                  <ShieldAlert size={24} />
                </div>
                <div className="text-[10px] font-black uppercase text-text-muted tracking-widest">No matching signals found in current frequency.</div>
              </div>
            ) : (
              filteredSignals.map((signal, index) => (
                <SignalCard 
                  key={signal.id} 
                  signal={signal} 
                  onClick={setSelectedSignal}
                  isSelected={selectedSignal?.id === signal.id}
                  style={{ animationDelay: `${index * 50}ms` }}
                  className="animate-in fade-in slide-in-from-top-4 duration-500"
                />
              ))
            )}
          </div>
        </div>
      </div>

      {selectedSignal && (
        <SignalDetailPanel 
          signal={selectedSignal}
          onDismiss={() => setSelectedSignal(null)}
          onExecute={handleExecuteSignal}
          isExecuting={isExecuting}
        />
      )}
    </div>
  );
}
