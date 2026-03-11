
"use client";

import { useState } from "react";
import { useFirestore, useUser, useCollection, useMemoFirebase } from "@/firebase";
import { collection, query, orderBy } from "firebase/firestore";
import { addDocumentNonBlocking } from "@/firebase/non-blocking-updates";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { ConfidencePill } from "@/components/shared/confidence-pill";
import { ScrollProgress } from "@/components/shared/scroll-progress";
import { GradientBorder } from "@/components/shared/gradient-border";
import { Signal, Position, Notification } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronRight, Target, Loader2, Play, Activity, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SignalsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Live Signals Stream
  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, "users", user.uid, "signals"), orderBy("createdAt", "desc"));
  }, [db, user]);

  const { data: signals, isLoading } = useCollection<Signal>(signalsQuery);

  function handleExecuteSignal() {
    if (!user || !db || !selectedSignal) return;
    setIsExecuting(true);

    const positionsRef = collection(db, "users", user.uid, "positions");
    const notificationsRef = collection(db, "users", user.uid, "notifications");

    const newPosition: Partial<Position> = {
      asset: selectedSignal.asset,
      direction: selectedSignal.direction,
      entryPrice: selectedSignal.entryPrice,
      currentPrice: selectedSignal.entryPrice,
      quantity: 1,
      unrealizedPnl: 0,
      unrealizedPnlPercent: 0,
      riskExposure: 2.5,
      signalId: selectedSignal.id,
      openedAt: new Date().toISOString(),
    };

    const newNotification: Partial<Notification> = {
      type: 'trade',
      title: 'Terminal Execution Successful',
      message: `Institutional ${selectedSignal.direction} position established for ${selectedSignal.asset} at $${selectedSignal.entryPrice.toLocaleString()}.`,
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
          <h2 className="text-2xl font-black uppercase">Signal Access Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to view real-time institutional-grade algorithmic signals.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <ScrollProgress />
      <div className="flex-1 p-8 space-y-8 overflow-y-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-black tracking-tight uppercase">Intelligence Stream</h1>
            <p className="text-muted-foreground text-sm">Real-time institutional-grade algorithmic signals and technical rationale.</p>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-4">
          {isLoading ? (
            Array(5).fill(0).map((_, i) => (
              <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
            ))
          ) : signals?.map((signal) => (
            <GradientBorder key={signal.id} active={signal.confidence >= 90}>
              <SpotlightCard 
                className={cn(
                  "p-6 cursor-pointer group transition-all h-full bg-transparent border-none",
                  selectedSignal?.id === signal.id && "bg-primary/5"
                )}
                onClick={() => setSelectedSignal(signal)}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "px-3 py-1 rounded text-[10px] font-black uppercase tracking-widest",
                      signal.direction === 'LONG' ? "bg-green/10 text-green" : "bg-red/10 text-red"
                    )}>
                      {signal.direction}
                    </div>
                    <div>
                      <div className="text-lg font-black tracking-tight">{signal.asset}</div>
                      <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest">{signal.strategy}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-12">
                    <div className="hidden md:block">
                      <div className="text-[9px] text-text-muted uppercase font-black tracking-widest mb-1">Execution Entry</div>
                      <div className="text-sm font-mono font-bold">${signal.entryPrice.toLocaleString()}</div>
                    </div>
                    <div className="flex items-center gap-6">
                      <ConfidencePill score={signal.confidence} />
                      <ChevronRight className={cn(
                        "text-text-muted transition-transform group-hover:translate-x-1",
                        selectedSignal?.id === signal.id && "rotate-90 md:rotate-0"
                      )} />
                    </div>
                  </div>
                </div>
              </SpotlightCard>
            </GradientBorder>
          ))}
        </div>
      </div>

      {selectedSignal && (
        <aside className="hidden lg:block w-[450px] border-l border-border-subtle bg-surface/80 backdrop-blur-xl p-8 overflow-y-auto space-y-8 animate-in slide-in-from-right duration-300">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black uppercase tracking-tighter text-primary">Institutional Detail</h2>
            <button 
              onClick={() => setSelectedSignal(null)}
              className="text-text-muted hover:text-text-primary text-[10px] font-black uppercase tracking-widest"
            >
              Dismiss
            </button>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-elevated/50 border border-border-subtle shadow-inner">
              <div className="flex items-center justify-between mb-6">
                <div className="text-3xl font-black tracking-tighter">{selectedSignal.asset}</div>
                <Badge className={cn(
                  "font-black uppercase tracking-widest",
                  selectedSignal.direction === 'LONG' ? "bg-green/10 text-green border-green/20" : "bg-red/10 text-red border-red/20"
                )}>
                  {selectedSignal.direction}
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle">
                  <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Invalidation (SL)</div>
                  <div className="text-sm font-mono font-bold text-red">${selectedSignal.stopLoss.toLocaleString()}</div>
                </div>
                <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle">
                  <div className="text-[9px] text-text-muted font-black uppercase mb-1.5">Target Projection</div>
                  <div className="text-sm font-mono font-bold text-green">${selectedSignal.takeProfit.toLocaleString()}</div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                <Activity size={14} className="text-primary" />
                Alpha Drivers
              </h3>
              <div className="space-y-3">
                {selectedSignal.drivers.map((driver, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 rounded-xl bg-elevated/20 border border-border-subtle">
                    <div className="w-1 h-1 rounded-full bg-primary" />
                    <span className="text-[11px] font-bold text-text-secondary uppercase">{driver}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-8 space-y-4">
             <Button 
                onClick={handleExecuteSignal}
                disabled={isExecuting}
                className="w-full h-16 bg-primary text-primary-foreground font-black uppercase text-xs hover:opacity-95 transition-all gap-3 shadow-[0_0_30px_rgba(96,165,250,0.4)] rounded-2xl"
              >
                {isExecuting ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
                Execute Signal Terminal
              </Button>
          </div>
        </aside>
      )}
    </div>
  );
}
