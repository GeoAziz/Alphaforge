'use client';

import { useState } from 'react';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Check, Copy, ExternalLink, Info, Terminal } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

export function TradingViewWebhookSetup() {
  const [copied, setCopied] = useState(false);
  const webhookUrl = "https://alphaforge.ai/api/webhooks/tradingview?token=node_7f8e_3a2b";

  const handleCopy = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Collapsible className="group">
      <SpotlightCard className="p-0 border-border-subtle overflow-hidden">
        <CollapsibleTrigger asChild>
          <div className="p-6 cursor-pointer hover:bg-elevated/20 transition-colors flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                <Terminal size={20} />
              </div>
              <div>
                <h3 className="text-sm font-black uppercase tracking-tight">Institutional Ingestion Setup</h3>
                <p className="text-[9px] text-text-muted font-bold uppercase tracking-widest">Connect TradingView Alerts • 3 Steps</p>
              </div>
            </div>
            <div className="text-[9px] font-black text-primary uppercase border border-primary/20 px-2 py-1 rounded">Expand Guide</div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent className="border-t border-border-subtle bg-elevated/10 animate-in slide-in-from-top-4 duration-300">
          <div className="p-8 space-y-10">
            {/* Step 1 */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-black">1</div>
                <h4 className="text-[11px] font-black uppercase tracking-widest text-text-primary">Authorize Node Webhook</h4>
              </div>
              <div className="flex items-center gap-2 p-4 rounded-xl bg-surface border border-border-subtle">
                <code className="text-[10px] font-mono font-bold text-text-secondary truncate flex-1">{webhookUrl}</code>
                <Button size="sm" variant="ghost" onClick={handleCopy} className="h-8 px-3 text-[9px] font-black uppercase gap-2 hover:bg-elevated">
                  {copied ? <Check size={12} className="text-green" /> : <Copy size={12} />}
                  {copied ? "Copied" : "Copy URL"}
                </Button>
              </div>
            </div>

            {/* Step 2 */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-black">2</div>
                <h4 className="text-[11px] font-black uppercase tracking-widest text-text-primary">Configure Alert Payload</h4>
              </div>
              <p className="text-[10px] text-text-muted font-bold uppercase leading-relaxed max-w-lg">
                Create an alert in TradingView and paste the following JSON into the "Message" field. Use double curly braces for dynamic variables.
              </p>
              <pre className="p-4 rounded-xl bg-inset border border-border-subtle text-[10px] font-mono text-primary leading-relaxed">
{`{
  "symbol": "{{exchange}}:{{ticker}}",
  "direction": "LONG",
  "confidence": 0.87,
  "node_id": "AF-NODE-01"
}`}
              </pre>
            </div>

            {/* Step 3 */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-black">3</div>
                <h4 className="text-[11px] font-black uppercase tracking-widest text-text-primary">Engage Ingestion</h4>
              </div>
              <div className="flex items-center gap-4">
                <Button variant="outline" className="border-border-subtle h-10 px-6 text-[10px] font-black uppercase gap-2 rounded-xl">
                  <ExternalLink size={14} /> TradingView Docs
                </Button>
                <div className="flex items-center gap-2 text-green">
                  <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
                  <span className="text-[9px] font-black uppercase">Endpoint Ready</span>
                </div>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </SpotlightCard>
    </Collapsible>
  );
}
