"use client";

import { useState, useEffect, useMemo } from "react";
import { useFirestore, useUser, useCollection, useMemoFirebase } from "@/firebase";
import { collection, query, orderBy } from "firebase/firestore";
import { addDocumentNonBlocking } from "@/firebase/non-blocking-updates";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { ConfidencePill } from "@/components/shared/confidence-pill";
import { GradientBorder } from "@/components/shared/gradient-border";
import { SignalDetailPanel } from "@/components/signals/signal-detail-panel";
import { Signal, Position, Notification } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronRight, ShieldAlert, Filter, Clock, Search, SlidersHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

export default function SignalsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [strategyFilter, setStrategyFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("active");
  const [confidenceRange, setConfidenceRange] = useState([0]);

  useEffect(() => setMounted(true), []);

  const signalsQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, "users", user.uid, "signals"), orderBy("createdAt", "desc"));
  }, [db, user]);

  const { data: rawSignals, isLoading } = useCollection<Signal>(signalsQuery);

  // Apply Client-Side Filters for responsiveness
  const filteredSignals = useMemo(() => {
    if (!rawSignals) return [];
    return rawSignals.filter(s => {
      const matchesSearch = s.asset.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStrategy = strategyFilter === "all" || s.strategy === strategyFilter;
      const matchesStatus = statusFilter === "all" || s.status === statusFilter;
      const matchesConfidence = s.confidence >= confidenceRange[0];
      return matchesSearch && matchesStrategy && matchesStatus && matchesConfidence;
    });
  }, [rawSignals, searchQuery, strategyFilter, statusFilter, confidenceRange]);

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

  const getSignalDecay = (createdAt: string) => {
    const age = Date.now() - new Date(createdAt).getTime();
    if (age > 3600000) return 'opacity-40 grayscale'; // 1hr
    if (age > 900000) return 'opacity-70'; // 15min
    return '';
  };

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
    <div className="flex h-full relative overflow-hidden animate-page">
      {/* Center Panel: Intelligence Stream */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="p-8 pb-4 space-y-6 border-b border-border-subtle bg-surface/50 backdrop-blur-md sticky top-0 z-20">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
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
          </div>

          {/* Filter Toolbar */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input 
                placeholder="Search assets..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-10 bg-elevated/30 border-border-subtle text-xs font-bold uppercase"
              />
            </div>
            <Select value={strategyFilter} onValueChange={setStrategyFilter}>
              <SelectTrigger className="w-[180px] h-10 bg-elevated/30 border-border-subtle text-xs font-black uppercase">
                <SelectValue placeholder="Strategy" />
              </SelectTrigger>
              <SelectContent className="glass">
                <SelectItem value="all">All Strategies</SelectItem>
                <SelectItem value="Momentum Breakout">Momentum Breakout</SelectItem>
                <SelectItem value="Mean Reversion">Mean Reversion</SelectItem>
                <SelectItem value="Volatility Expansion">Volatility Expansion</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px] h-10 bg-elevated/30 border-border-subtle text-xs font-black uppercase">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="glass">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="flex items-center gap-4 px-4 h-10 rounded-lg bg-elevated/30 border border-border-subtle min-w-[200px]">
              <span className="text-[9px] font-black uppercase text-text-muted whitespace-nowrap">Min Confidence: {confidenceRange[0]}%</span>
              <Slider 
                value={confidenceRange} 
                onValueChange={setConfidenceRange} 
                max={100} 
                step={5} 
                className="flex-1"
              />
            </div>
          </div>
        </header>

        <div className="flex-1 p-8 space-y-4 overflow-y-auto scrollbar-hide pb-24 md:pb-8">
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
          ) : filteredSignals.map((signal, index) => (
            <div 
              key={signal.id} 
              style={{ transitionDelay: `${index * 50}ms` }}
              className={cn(
                "transition-all duration-500 transform translate-y-0",
                !mounted && "translate-y-4 opacity-0",
                getSignalDecay(signal.createdAt)
              )}
            >
              <GradientBorder active={signal.confidence >= 85}>
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
                        <div className="text-xl font-black tracking-tighter group-hover:text-primary transition-colors">{signal.asset}</div>
                        <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest flex items-center gap-2">
                          {signal.strategy}
                          <div className="w-1 h-1 rounded-full bg-border-subtle" />
                          <span className="flex items-center gap-1"><Clock size={10} /> {new Date(signal.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-12">
                      <div className="hidden md:block">
                        <div className="text-[9px] text-text-muted uppercase font-black tracking-widest mb-1">Entry Threshold</div>
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
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel: Terminal Detail */}
      <SignalDetailPanel 
        signal={selectedSignal}
        onDismiss={() => setSelectedSignal(null)}
        onExecute={handleExecuteSignal}
        isExecuting={isExecuting}
      />
    </div>
  );
}
