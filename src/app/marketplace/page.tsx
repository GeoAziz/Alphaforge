'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { MarketplaceStrategy, Notification } from '@/lib/types';
import { Users, CheckCircle2, TrendingUp, ShieldAlert, ShoppingBag, Loader2, Star, ShieldCheck, Zap, Info, ArrowRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

export default function MarketplacePage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedStrategy, setSelectedStrategy] = useState<MarketplaceStrategy | null>(null);
  const [subscribingId, setSubscribingId] = useState<string | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const marketplaceQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketplaceStrategies'), orderBy('subscribers', 'desc'));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<MarketplaceStrategy>(marketplaceQuery);

  function handleSubscribeInitiate(strategy: MarketplaceStrategy) {
    setSelectedStrategy(strategy);
    setShowDisclaimer(true);
  }

  function handleFinalizeSubscription() {
    if (!user || !db || !selectedStrategy) return;
    setSubscribingId(selectedStrategy.id);
    setShowDisclaimer(false);

    const subscriptionRef = doc(db, 'users', user.uid, 'subscriptions', selectedStrategy.id);
    const notificationRef = doc(collection(db, 'users', user.uid, 'notifications'));

    setDocumentNonBlocking(subscriptionRef, { 
      strategyId: selectedStrategy.id,
      subscribedAt: new Date().toISOString(),
      status: 'paper_trade' // Default to paper trade gate
    }, { merge: true });

    const notification: Partial<Notification> = {
      type: 'system',
      userId: user.uid,
      title: 'Node Sync Initialized',
      message: `Successfully established communication with ${selectedStrategy.name}. Paper trading session enabled for terminal verification.`,
      read: false,
      critical: false,
      createdAt: new Date().toISOString(),
    };
    setDocumentNonBlocking(notificationRef, notification, { merge: true });

    setTimeout(() => {
      setSubscribingId(null);
      setSelectedStrategy(null);
    }, 1500);
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShoppingBag size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Marketplace restricted</h2>
          <p className="text-sm text-text-muted">Establish an institutional handshake to access verified algorithmic strategy subscriptions from top-tier providers.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Signal Marketplace</h1>
        <p className="text-muted-foreground text-sm">Subscribe to verified institutional-grade algorithmic engines from globally distributed providers.</p>
      </header>

      {/* Institutional Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
            <ShieldCheck size={20} />
          </div>
          <div>
            <div className="text-[10px] font-black uppercase text-primary">Verification Core</div>
            <div className="text-sm font-bold">5-Stage Audit Pipeline</div>
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-amber/5 border border-amber/10 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber/20 flex items-center justify-center text-amber">
            <Zap size={20} />
          </div>
          <div>
            <div className="text-[10px] font-black uppercase text-amber">Latency Sync</div>
            <div className="text-sm font-bold">Sub-10ms Signal Relay</div>
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-green/5 border border-green/10 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-green/20 flex items-center justify-center text-green">
            <TrendingUp size={20} />
          </div>
          <div>
            <div className="text-[10px] font-black uppercase text-green">Alpha Verified</div>
            <div className="text-sm font-bold">Consensus ROI Tracking</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-80 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
          ))
        ) : strategies?.map((strategy) => (
          <SpotlightCard key={strategy.id} variant="accent" className="p-8 flex flex-col md:flex-row gap-8 group">
            <div className="flex-1 space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-elevated flex items-center justify-center text-xl font-black border border-border-subtle shadow-inner">
                    {strategy.name[0]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-2xl font-black tracking-tight group-hover:text-primary transition-colors">{strategy.name}</h3>
                      {strategy.isVerified && (
                        <div className="text-primary" title="Verified Provider Tier 5">
                          <CheckCircle2 size={18} fill="currentColor" className="text-primary-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest">
                      By <span className="text-text-primary underline decoration-primary/50 underline-offset-4 cursor-help">{strategy.creator}</span>
                      <div className="w-1 h-1 rounded-full bg-text-muted" />
                      <div className="flex items-center text-amber gap-0.5">
                        <Star size={10} fill="currentColor" /> 4.9 Rep
                      </div>
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className={cn(
                  "text-[10px] font-black uppercase tracking-widest border-primary/30",
                  strategy.riskLevel === 'High' ? "text-red border-red/30" : "text-primary"
                )}>
                  {strategy.riskLevel} Risk
                </Badge>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed line-clamp-3">
                {strategy.description}
              </p>

              <div className="flex flex-wrap gap-6 pt-4 border-t border-border-subtle/50">
                <div className="space-y-1">
                  <div className="text-[9px] font-black text-text-muted uppercase tracking-widest">Subscribers</div>
                  <div className="flex items-center gap-2 text-sm font-black">
                    <Users size={14} className="text-primary" />
                    {strategy.subscribers.toLocaleString()}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-[9px] font-black text-text-muted uppercase tracking-widest">Efficiency</div>
                  <div className="flex items-center gap-2 text-sm font-black text-green">
                    <TrendingUp size={14} />
                    {strategy.winRate}%
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-[9px] font-black text-text-muted uppercase tracking-widest">Drawdown</div>
                  <div className="flex items-center gap-2 text-sm font-black text-red">
                    <ShieldAlert size={14} />
                    {strategy.maxDrawdown}%
                  </div>
                </div>
              </div>
            </div>

            <div className="w-full md:w-60 flex flex-col justify-between border-l border-border-subtle md:pl-8 pt-8 md:pt-0">
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle shadow-inner">
                  <div className="text-[9px] font-black uppercase tracking-widest text-text-muted mb-1">ROI Trailing 12M</div>
                  <div className="text-4xl font-black text-green font-mono tracking-tighter">+{strategy.roi}%</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-[9px] font-black uppercase text-primary">
                    <CheckCircle2 size={10} /> 5-Stage Verified
                  </div>
                  <div className="flex gap-1">
                    {Array(5).fill(0).map((_, i) => (
                      <div key={i} className="h-1 flex-1 rounded-full bg-primary" />
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8 space-y-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-[10px] font-black uppercase text-text-muted">Subscription</span>
                  <div className="text-xl font-black font-mono">${strategy.monthlyPrice}<span className="text-xs font-bold text-text-muted">/mo</span></div>
                </div>
                <Button 
                  onClick={() => handleSubscribeInitiate(strategy)}
                  disabled={subscribingId === strategy.id}
                  className="w-full bg-primary text-primary-foreground font-black uppercase text-xs h-12 gap-2 shadow-[0_0_25px_rgba(96,165,250,0.3)] rounded-2xl group-hover:scale-[1.02] transition-transform"
                >
                  {subscribingId === strategy.id ? <Loader2 className="animate-spin" size={16} /> : <ShoppingBag size={16} />}
                  Synchronize Node
                </Button>
              </div>
            </div>
          </SpotlightCard>
        ))}
      </div>

      {/* Disclaimer Modal */}
      <Dialog open={showDisclaimer} onOpenChange={setShowDisclaimer}>
        <DialogContent className="glass border-border-subtle sm:max-w-[500px] p-8">
          <DialogHeader className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber/10 flex items-center justify-center text-amber border border-amber/20">
              <ShieldAlert size={24} />
            </div>
            <DialogTitle className="text-2xl font-black uppercase tracking-tight leading-none">Institutional Protocol Acknowledgement</DialogTitle>
            <DialogDescription className="text-text-secondary leading-relaxed">
              You are about to synchronize your node with a third-party algorithmic cluster. Please acknowledge the following institutional protocols:
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex gap-3 items-start">
              <div className="mt-1"><Info size={14} className="text-primary" /></div>
              <p className="text-[11px] text-text-muted font-medium uppercase">All new subscriptions are gated behind a 7-day paper trading verification session to ensure node-to-node latency parity.</p>
            </div>
            <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex gap-3 items-start">
              <div className="mt-1"><ShieldCheck size={14} className="text-green" /></div>
              <p className="text-[11px] text-text-muted font-medium uppercase">Past performance is not indicative of future alpha. AlphaForge verification core focuses on strategy integrity, not guaranteed yield.</p>
            </div>
          </div>
          <DialogFooter className="flex flex-col sm:flex-row gap-3">
            <Button variant="ghost" onClick={() => setShowDisclaimer(false)} className="h-12 font-black uppercase text-[10px]">Cancel Handshake</Button>
            <Button onClick={handleFinalizeSubscription} className="flex-1 h-12 bg-primary text-primary-foreground font-black uppercase text-[10px] gap-2">
              Acknowledge & Sync <ArrowRight size={14} />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
