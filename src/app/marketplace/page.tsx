'use client';

import { useState, useMemo } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy, doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { MarketplaceStrategy, Notification } from '@/lib/types';
import { 
  ShieldAlert, ShoppingBag, Loader2, Zap, ArrowRight, 
  Search, SlidersHorizontal, Award, Sparkles, Filter, Check
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter 
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from '@/lib/utils';
import { VerificationBadge } from '@/components/shared/verification-badge';
import { ReputationScore } from '@/components/shared/reputation-score';
import { useIsMobile } from '@/hooks/use-mobile';

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
  const [agreedTerms, setAgreedTerms] = useState({
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
      message: `Established connection with ${selectedStrategy.name}. Paper trading active.`,
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

  const DisclaimerContent = () => (
    <>
      <div className="p-6 lg:p-8 pb-4 space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 lg:w-14 lg:h-14 rounded-2xl bg-amber/10 flex items-center justify-center text-amber border border-amber/20 shadow-inner">
            <ShieldAlert size={24} />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl lg:text-2xl font-black uppercase tracking-tighter leading-none">Operating Protocol</h2>
            <p className="text-[9px] lg:text-[10px] text-text-muted font-bold uppercase tracking-widest">Handshake Verification AF-2024</p>
          </div>
        </div>
        <p className="text-text-secondary text-[11px] lg:text-xs leading-relaxed font-medium uppercase">
          A node connection requires explicit acknowledgement of the AlphaForge Institutional Operating Protocols.
        </p>
      </div>

      <div className="max-h-[300px] lg:max-h-[400px] overflow-y-auto px-6 lg:px-8 py-4 space-y-4 lg:space-y-6 scrollbar-hide border-y border-border-subtle bg-surface/30">
        <div className="space-y-3 p-4 rounded-xl border border-red/20 bg-red/5">
          <div className="flex items-start gap-3">
            <Checkbox id="term-risk" checked={agreedTerms.risk} onCheckedChange={(v) => setAgreedTerms(prev => ({...prev, risk: v as boolean}))} />
            <Label htmlFor="term-risk" className="text-[9px] lg:text-[10px] font-bold text-red uppercase leading-snug cursor-pointer">
              I acknowledge that algorithmic trading involves substantial risk. Past alpha is not an indicator of future performance.
            </Label>
          </div>
        </div>
        <div className="space-y-3 p-4 rounded-xl border border-amber/20 bg-amber/5">
          <div className="flex items-start gap-3">
            <Checkbox id="term-performance" checked={agreedTerms.performance} onCheckedChange={(v) => setAgreedTerms(prev => ({...prev, performance: v as boolean}))} />
            <Label htmlFor="term-performance" className="text-[9px] lg:text-[10px] font-bold text-amber uppercase leading-snug cursor-pointer">
              I understand that backtest results are simulated and may not reflect live execution slippage.
            </Label>
          </div>
        </div>
        <div className="space-y-3 p-4 rounded-xl border border-primary/20 bg-primary/5">
          <div className="flex items-start gap-3">
            <Checkbox id="term-latency" checked={agreedTerms.latency} onCheckedChange={(v) => setAgreedTerms(prev => ({...prev, latency: v as boolean}))} />
            <Label htmlFor="term-latency" className="text-[9px] lg:text-[10px] font-bold text-primary uppercase leading-snug cursor-pointer">
              New nodes are gated behind a 7-day paper-trading verification period to ensure latency parity.
            </Label>
          </div>
        </div>
        <div className="flex items-center gap-3 px-2">
          <Checkbox id="term-confirmation" checked={agreedTerms.confirmation} onCheckedChange={(v) => setAgreedTerms(prev => ({...prev, confirmation: v as boolean}))} />
          <Label htmlFor="term-confirmation" className="text-[10px] lg:text-[11px] font-black text-text-primary uppercase cursor-pointer">
            Authorize AlphaForge node connection.
          </Label>
        </div>
      </div>
    </>
  );

  const FooterButtons = () => (
    <div className="p-6 lg:p-8 bg-elevated/10 flex flex-col sm:flex-row gap-4">
      <Button variant="ghost" onClick={() => setShowDisclaimer(false)} className="h-12 font-black uppercase text-[10px] tracking-widest text-text-muted hover:text-text-primary touch-target">
        Cancel
      </Button>
      <Button disabled={!allAgreed} onClick={handleFinalizeSubscription} className="flex-1 h-12 bg-primary text-primary-foreground font-black uppercase text-[10px] gap-2 rounded-xl shadow-lg touch-target">
        Finalize Sync <ArrowRight size={14} />
      </Button>
    </div>
  );

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
    <div className="p-8 space-y-8 pb-20 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Strategy Marketplace</h1>
        <p className="text-muted-foreground text-sm font-medium">Subscribe to verified institutional-grade algorithmic engines.</p>
      </header>

      {/* Top Creators Node */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 px-2">
          <Award size={16} className="text-accent" />
          <h3 className="text-[10px] font-black uppercase tracking-widest text-text-muted">Institutional Providers</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
          {topCreators.map(creator => (
            <SpotlightCard key={creator.name} className="p-6 border-accent/10 bg-accent/5">
              <div className="flex justify-between items-start mb-4">
                <div className="space-y-1">
                  <div className="text-lg font-black tracking-tighter">{creator.name}</div>
                  <ReputationScore score={creator.rep} />
                </div>
                <Badge variant="outline" className="text-[8px] font-black border-accent/20 text-accent uppercase">Tier 1</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 border-t border-border-subtle/50 pt-4">
                <div>
                  <div className="text-[8px] font-black text-text-muted uppercase">Active</div>
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

      {/* Filter Toolbar */}
      <div className="flex flex-col lg:flex-row items-center gap-4 bg-elevated/20 p-4 rounded-2xl border border-border-subtle sticky top-4 z-30 backdrop-blur-xl">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input 
            placeholder="Search strategies..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-12 bg-surface/50 border-border-subtle text-xs font-bold uppercase"
          />
        </div>
        <div className="flex items-center gap-2 w-full lg:w-auto overflow-x-auto scrollbar-hide pb-1 lg:pb-0">
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

      {/* Strategy Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-[400px] rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />
          ))
        ) : filteredStrategies.map((strategy) => (
          <SpotlightCard key={strategy.id} variant="accent" className="p-0 flex flex-col border-primary/5 hover:border-primary/20 transition-all group overflow-hidden">
            <div className="p-6 lg:p-8 flex-1 space-y-6 lg:space-y-8">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-2xl bg-elevated flex items-center justify-center text-xl font-black border border-border-subtle shadow-inner">
                    {strategy.name[0]}
                  </div>
                  <div>
                    <h3 className="text-xl lg:text-2xl font-black tracking-tighter group-hover:text-primary leading-none">{strategy.name}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="text-[9px] font-bold text-text-muted uppercase tracking-widest">{strategy.creator}</span>
                      <ReputationScore score={strategy.reputationScore} />
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className={cn(
                  "text-[9px] font-black uppercase border-primary/20",
                  strategy.riskLevel === 'High' ? "text-red border-red/20" : "text-primary"
                )}>
                  {strategy.riskLevel}
                </Badge>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed font-medium line-clamp-3">
                {strategy.description}
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 lg:gap-4">
                {[
                  { l: 'Efficiency', v: `${strategy.winRate}%`, c: 'text-green' },
                  { l: 'Drawdown', v: `${strategy.maxDrawdown}%`, c: 'text-red' },
                  { l: 'Nodes', v: strategy.subscribers.toLocaleString(), c: 'text-text-primary' },
                  { l: 'Delta', v: `${strategy.paperTradeDelta! >= 0 ? '+' : ''}${strategy.paperTradeDelta}%`, c: (strategy.paperTradeDelta || 0) >= 0 ? 'text-green' : 'text-red' }
                ].map(m => (
                  <div key={m.l} className="p-3 rounded-xl bg-surface border border-border-subtle space-y-1">
                    <div className="text-[8px] font-black text-text-muted uppercase">{m.l}</div>
                    <div className={cn("text-xs lg:text-sm font-black font-mono", m.c)}>{m.v}</div>
                  </div>
                ))}
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-border-subtle/50">
                <VerificationBadge stage={strategy.verificationStage} className="w-full sm:w-auto" />
                <div className="text-right w-full sm:w-auto">
                  <div className="text-[9px] font-black uppercase text-text-muted mb-1">ROI Trailing 12M</div>
                  <div className="text-3xl lg:text-4xl font-black text-green font-mono tracking-tighter">+{strategy.roi}%</div>
                </div>
              </div>
            </div>

            <div className="bg-elevated/30 border-t border-border-subtle p-6 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-6 w-full sm:w-auto">
                <div className="space-y-1">
                  <div className="text-[9px] font-black uppercase text-text-muted">Node Fee</div>
                  <div className="text-xl font-black font-mono">${strategy.monthlyPrice}<span className="text-[10px] text-text-muted">/mo</span></div>
                </div>
                <div className="h-8 w-px bg-border-subtle" />
                <Badge variant="outline" className="text-[8px] font-black uppercase border-primary/20 text-primary">{strategy.pricingModel}</Badge>
              </div>
              
              <Button 
                onClick={() => handleSubscribeInitiate(strategy)}
                disabled={subscribingId === strategy.id}
                className="w-full sm:w-[180px] bg-primary text-primary-foreground font-black uppercase text-[10px] h-12 gap-2 rounded-xl group-hover:scale-[1.02] transition-transform touch-target"
              >
                {subscribingId === strategy.id ? <Loader2 className="animate-spin" size={16} /> : <ShoppingBag size={16} />}
                Establish Sync
              </Button>
            </div>
          </SpotlightCard>
        ))}
      </div>

      {/* Institutional Disclaimer - Sheet on Mobile, Dialog on Desktop */}
      {isMobile ? (
        <Sheet open={showDisclaimer} onOpenChange={setShowDisclaimer}>
          <SheetContent side="bottom" className="glass border-border-subtle h-[90vh] p-0 rounded-t-3xl overflow-hidden shadow-2xl">
            <DisclaimerContent />
            <div className="mt-auto">
              <FooterButtons />
            </div>
          </SheetContent>
        </Sheet>
      ) : (
        <Dialog open={showDisclaimer} onOpenChange={setShowDisclaimer}>
          <DialogContent className="glass border-border-subtle sm:max-w-[600px] p-0 overflow-hidden shadow-2xl">
            <DisclaimerContent />
            <FooterButtons />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
