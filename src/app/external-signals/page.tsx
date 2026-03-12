'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { ExternalSignal, WebhookEvent, SignalIngestionRule } from '@/lib/types';
import { TradingViewWebhookSetup } from '@/components/external-signals/tradingview-webhook-setup';
import { IngestionRulesPanel } from '@/components/external-signals/ingestion-rules-panel';
import { ExternalSignalFeed } from '@/components/external-signals/external-signal-feed';
import { WebhookHistory } from '@/components/external-signals/webhook-history';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Zap, Share2, ShieldAlert } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function ExternalSignalsPage() {
  const { user } = useUser();
  const [signals, setSignals] = useState<ExternalSignal[]>([]);
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [rule, setRule] = useState<SignalIngestionRule | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      Promise.all([
        api.external.getSignals(user.uid),
        api.external.getWebhookEvents(user.uid),
        api.external.getIngestionRule(user.uid)
      ]).then(([s, e, r]) => {
        setSignals(s);
        setEvents(e);
        setRule(r);
        setIsLoading(false);
      });
    }
  }, [user]);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Zap size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Ingestion Restricted</h2>
          <p className="text-sm text-text-muted">Establish institutional handshake to activate external signal nodes.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-32 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">External Intelligence</h1>
        <p className="text-muted-foreground text-sm font-medium">Bridge TradingView alerts and third-party algorithmic nodes into AlphaForge execution.</p>
      </header>

      <div className="grid grid-cols-1 gap-8">
        {/* Setup Guide */}
        <TradingViewWebhookSetup />

        {/* Rules Engine */}
        {rule && <IngestionRulesPanel initialRule={rule} />}

        {/* Feed and Activity Tabs */}
        <Tabs defaultValue="feed" className="space-y-6">
          <div className="flex items-center justify-between border-b border-border-subtle">
            <TabsList className="bg-transparent h-auto p-0 gap-8">
              <TabsTrigger value="feed" className="px-0 pb-3 font-black uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
                Ingested Signals
              </TabsTrigger>
              <TabsTrigger value="history" className="px-0 pb-3 font-black uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
                Webhook Activity
              </TabsTrigger>
            </TabsList>
            <div className="flex items-center gap-2 text-[9px] font-black text-text-muted uppercase tracking-widest pb-3">
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
              Ingest Node: Online
            </div>
          </div>

          <TabsContent value="feed" className="mt-0 outline-none">
            <ExternalSignalFeed signals={signals} isLoading={isLoading} />
          </TabsContent>

          <TabsContent value="history" className="mt-0 outline-none">
            <WebhookHistory events={events} isLoading={isLoading} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
