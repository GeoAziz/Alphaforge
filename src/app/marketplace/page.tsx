'use client';

import { useState, useMemo } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { MarketplaceStrategy, Notification } from '@/lib/types';
import { 
  ShoppingBag, 
  Search, 
  Award, 
  ArrowRight
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Dialog, 
  DialogContent 
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ReputationScore } from '@/components/shared/reputation-score';
import { useIsMobile } from '@/hooks/use-mobile';
import { MarketplaceGrid } from '@/components/marketplace/marketplace-grid';
import { MarketplaceDisclaimer } from '@/components/marketplace/marketplace-disclaimer';

export default function MarketplacePage() {
  const { user } = useUser();
  const db = useFirestore();
  const isMobile = useIsMobile();
  const [selectedStrategy, setSelectedStrategy] = useState<MarketplaceStrategy | null>(null);
  const [subscribingId, setSubscribingId] = useState<string | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [pricingFilter, setPricingFilter] = useState("all");
  
  // Disclaimer Checkbox States
  const [agreedTerms, setAgreedTerms] = useState<Record<string, boolean>>({
    risk: false,
    performance: false,
    latency: false,
    pricing: false,
    confirmation: false
  });

  const marketplaceQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'marketplaceStrategies'), orderBy('subscribers', 'desc'));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<MarketplaceStrategy>(marketplaceQuery);

  const filteredStrategies = useMemo(() => {
    if (!strategies) return [];
    return strategies.filter(s => {
      const matchesSearch = s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           s.creator.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesRisk = riskFilter === "all" || s.riskLevel === riskFilter;
      const matchesPricing = pricingFilter === "all" || s.pricingModel === pricingFilter;
      return matchesSearch && matchesRisk && matchesPricing;
    });
  }, [strategies, searchQuery, riskFilter, pricingFilter]);

  const topCreators = [
    { name: 'Cipher Capital', rep: 4.9, active: 12, assets: '$42M' },
    { name: 'AlphaForge Labs', rep: 4.7, active: 8, assets: '$18M' },
    { name: 'Vertex Node', rep: 4.5, active: 5, assets: '$9M' },
  ];

  function handleSubscribeInitiate(strategy: MarketplaceStrategy) {
    setSelectedStrategy(strategy);
    setAgreedTerms({ risk: false, performance: false, latency: false, pricing: false, confirmation: false });
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
      status: 'paper_trade' 
    }, { merge: true });

    const notification: Partial<Notification> = {
      type: 'system',
      userId: user.uid,
      title: 'Node Sync Initialized',
      message: `Established institutional handshake with ${selectedStrategy.name}. Paper trading node activated.`,
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

  const allAgreed = Object.values(agreedTerms).every(v => v);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShoppingBag size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Marketplace restricted</h2>
          <p className="text-sm text-text-muted">Establish an institutional handshake to access verified algorithmic strategy nodes.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Strategy Marketplace</h1>
        <p className="text-muted-foreground text-sm font-medium uppercase tracking-tight">Subscribe to verified institutional-grade algorithmic engines.</p>
      </header>

      {/* Top Providers */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 px-2">
          <Award size={16} className="text-accent" />
          <h3 className="text-[10px] font-black uppercase tracking-widest text-text-muted">Institutional Providers</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {topCreators.map(creator => (
            <SpotlightCard key={creator.name} className="p-6 border-accent/10 bg-accent/5">
              <div className="flex justify-between items-start mb-4">
                <div className="space-y-1">
                  <div className="text-lg font-black tracking-tighter uppercase">{creator.name}</div>
                  <ReputationScore score={creator.rep} />
                </div>
                <Badge variant="outline" className="text-[8px] font-black border-accent/20 text-accent uppercase">Tier 1</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 border-t border-border-subtle/50 pt-4">
                <div>
                  <div className="text-[8px] font-black text-text-muted uppercase">Nodes</div>
                  <div className="text-xs font-bold">{creator.active} Strats</div>
                </div>
                <div>
                  <div className="text-[8px] font-black text-text-muted uppercase">AUM</div>
                  <div className="text-xs font-bold text-accent">{creator.assets}</div>
                </div>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </div>

      {/* Traversal Toolbar */}
      <div className="flex flex-col lg:flex-row items-center gap-4 bg-elevated/20 p-4 rounded-2xl border border-border-subtle sticky top-4 z-30 backdrop-blur-xl shadow-2xl">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input 
            placeholder="Search strategy clusters..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-12 bg-surface/50 border-border-subtle text-[10px] font-black uppercase tracking-widest"
          />
        </div>
        <div className="flex items-center gap-2 w-full lg:w-auto">
          <Select value={riskFilter} onValueChange={setRiskFilter}>
            <SelectTrigger className="flex-1 lg:w-[140px] h-12 bg-surface/50 border-border-subtle text-[10px] font-black uppercase">
              <SelectValue placeholder="Risk" />
            </SelectTrigger>
            <SelectContent className="glass">
              <SelectItem value="all">All Risk</SelectItem>
              <SelectItem value="Low">Low</SelectItem>
              <SelectItem value="Medium">Medium</SelectItem>
              <SelectItem value="High">High</SelectItem>
            </SelectContent>
          </Select>
          <Select value={pricingFilter} onValueChange={setPricingFilter}>
            <SelectTrigger className="flex-1 lg:w-[160px] h-12 bg-surface/50 border-border-subtle text-[10px] font-black uppercase">
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent className="glass">
              <SelectItem value="all">All Models</SelectItem>
              <SelectItem value="Subscription">Subscription</SelectItem>
              <SelectItem value="Profit Share">Profit Share</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <MarketplaceGrid 
        strategies={filteredStrategies} 
        onSubscribe={handleSubscribeInitiate}
        subscribingId={subscribingId}
        isLoading={isLoading}
      />

      {/* Subscription Disclaimer */}
      {isMobile ? (
        <Sheet open={showDisclaimer} onOpenChange={setShowDisclaimer}>
          <SheetContent side="bottom" className="glass border-border-subtle h-[90vh] p-0 rounded-t-3xl overflow-hidden">
            <MarketplaceDisclaimer 
              agreedTerms={agreedTerms} 
              onToggleTerm={(k, v) => setAgreedTerms(prev => ({...prev, [k]: v}))} 
            />
            <div className="p-6 bg-elevated/10 border-t border-border-subtle">
              <Button disabled={!allAgreed} onClick={handleFinalizeSubscription} className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 rounded-2xl shadow-xl">
                Finalize Node Sync <ArrowRight size={16} />
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      ) : (
        <Dialog open={showDisclaimer} onOpenChange={setShowDisclaimer}>
          <DialogContent className="glass border-border-subtle sm:max-w-[600px] p-0 overflow-hidden shadow-2xl">
            <MarketplaceDisclaimer 
              agreedTerms={agreedTerms} 
              onToggleTerm={(k, v) => setAgreedTerms(prev => ({...prev, [k]: v}))} 
            />
            <div className="p-8 bg-elevated/10 border-t border-border-subtle flex gap-4">
              <Button variant="ghost" onClick={() => setShowDisclaimer(false)} className="flex-1 h-14 font-black uppercase text-xs">
                Abort Sync
              </Button>
              <Button disabled={!allAgreed} onClick={handleFinalizeSubscription} className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 rounded-2xl shadow-xl">
                Finalize Node Sync <ArrowRight size={16} />
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
