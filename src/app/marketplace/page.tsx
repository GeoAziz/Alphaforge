'use client';

import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { MarketplaceStrategy, Notification } from '@/lib/types';
import { Users, CheckCircle2, TrendingUp, ShieldAlert, ShoppingBag, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export default function MarketplacePage() {
  const { user } = useUser();
  const db = useFirestore();
  const [subscribingId, setSubscribingId] = useState<string | null>(null);

  const marketplaceQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketplaceStrategies'), orderBy('subscribers', 'desc'));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<MarketplaceStrategy>(marketplaceQuery);

  function handleSubscribe(strategy: MarketplaceStrategy) {
    if (!user || !db) return;
    setSubscribingId(strategy.id);

    const subscriptionRef = doc(db, 'users', user.uid, 'subscriptions', strategy.id);
    const notificationRef = doc(collection(db, 'users', user.uid, 'notifications'));

    setDocumentNonBlocking(subscriptionRef, { 
      strategyId: strategy.id,
      subscribedAt: new Date().toISOString()
    }, { merge: true });

    const notification: Partial<Notification> = {
      type: 'system',
      title: 'Subscription Established',
      message: `Node has successfully synchronized with ${strategy.name} signals. Live updates enabled.`,
      read: false,
      critical: false,
      createdAt: new Date().toISOString(),
    };
    setDocumentNonBlocking(notificationRef, notification, { merge: true });

    setTimeout(() => setSubscribingId(null), 1000);
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Marketplace Access Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to subscribe to verified institutional-grade signals from top-tier providers.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Signal Marketplace</h1>
        <p className="text-muted-foreground text-sm">Subscribe to verified institutional-grade signals from top-tier providers.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-80 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
          ))
        ) : strategies?.map((strategy) => (
          <SpotlightCard key={strategy.id} variant="accent" className="p-8 flex flex-col md:flex-row gap-8">
            <div className="flex-1 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="text-2xl font-black tracking-tight">{strategy.name}</h3>
                  {strategy.isVerified && (
                    <div className="text-primary" title="Verified Provider">
                      <CheckCircle2 size={18} fill="currentColor" className="text-primary-foreground" />
                    </div>
                  )}
                </div>
                <Badge variant="outline" className="text-[10px] font-black uppercase tracking-widest border-primary/30 text-primary">
                  {strategy.riskLevel} Risk
                </Badge>
              </div>

              <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest">
                By <span className="text-text-primary underline decoration-primary/50 underline-offset-4">{strategy.creator}</span>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">
                {strategy.description}
              </p>

              <div className="flex flex-wrap gap-4 pt-4">
                <div className="flex items-center gap-2 text-xs font-bold text-text-muted">
                  <Users size={14} className="text-primary" />
                  {strategy.subscribers.toLocaleString()} Subscribers
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-text-muted">
                  <TrendingUp size={14} className="text-green" />
                  {strategy.winRate}% Win Rate
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-text-muted">
                  <ShieldAlert size={14} className="text-red" />
                  {strategy.maxDrawdown}% Max DD
                </div>
              </div>
            </div>

            <div className="w-full md:w-56 flex flex-col justify-between border-l border-border-subtle md:pl-8 pt-8 md:pt-0">
              <div className="space-y-1">
                <div className="text-[10px] font-black uppercase tracking-widest text-text-muted">ROI Trailing 12M</div>
                <div className="text-4xl font-black text-green font-mono">+{strategy.roi}%</div>
              </div>

              <div className="mt-8 space-y-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-[10px] font-black uppercase text-text-muted">Price</span>
                  <div className="text-xl font-black font-mono">${strategy.monthlyPrice}<span className="text-xs font-bold text-text-muted">/mo</span></div>
                </div>
                <Button 
                  onClick={() => handleSubscribe(strategy)}
                  disabled={subscribingId === strategy.id}
                  className="w-full bg-primary text-primary-foreground font-black uppercase text-xs h-12 gap-2 shadow-[0_0_20px_rgba(96,165,250,0.3)]"
                >
                  {subscribingId === strategy.id ? <Loader2 className="animate-spin" size={16} /> : <ShoppingBag size={16} />}
                  Subscribe Now
                </Button>
              </div>
            </div>
          </SpotlightCard>
        ))}
      </div>
    </div>
  );
}