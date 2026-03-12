'use client';

import { ShieldAlert, AlertTriangle, ShieldCheck, Zap, Info } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface MarketplaceDisclaimerProps {
  agreedTerms: Record<string, boolean>;
  onToggleTerm: (key: string, value: boolean) => void;
}

/**
 * MarketplaceDisclaimer - Multi-section regulatory handshake for strategy node sync.
 */
export function MarketplaceDisclaimer({ agreedTerms, onToggleTerm }: MarketplaceDisclaimerProps) {
  const terms = [
    {
      id: 'risk',
      icon: ShieldAlert,
      color: 'text-red',
      bg: 'bg-red/5',
      border: 'border-red/20',
      label: 'Algorithmic Risk Disclosure',
      text: 'I acknowledge that high-frequency trading involves substantial risk of total capital loss. Models can fail without warning during black swan events.'
    },
    {
      id: 'performance',
      icon: AlertTriangle,
      color: 'text-amber',
      bg: 'bg-amber/5',
      border: 'border-amber/20',
      label: 'Simulated Data Acknowledgement',
      text: 'I understand that past performance, including backtest and paper-trade results, is not an indicator of future alpha or execution parity.'
    },
    {
      id: 'latency',
      icon: Zap,
      color: 'text-primary',
      bg: 'bg-primary/5',
      border: 'border-primary/20',
      label: 'Network Latency Sync',
      text: 'New node syncs are subject to a mandatory 7-day monitoring phase. Real execution may differ from the node trigger by up to 150ms.'
    },
    {
      id: 'pricing',
      icon: Info,
      color: 'text-accent',
      bg: 'bg-accent/5',
      border: 'border-accent/20',
      label: 'Financial Handshake Protocol',
      text: 'I authorize the selected node billing model (Subscription or Profit-Share) and acknowledge that fees are non-refundable after handshake.'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="p-6 lg:p-8 pb-4 space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 lg:w-14 lg:h-14 rounded-2xl bg-elevated flex items-center justify-center text-primary border border-border-subtle shadow-inner">
            <ShieldCheck size={24} />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl lg:text-2xl font-black uppercase tracking-tighter leading-none">Operating Protocol</h2>
            <p className="text-[9px] lg:text-[10px] text-text-muted font-bold uppercase tracking-widest">Handshake Verification AF-2024</p>
          </div>
        </div>
        <p className="text-text-secondary text-[11px] lg:text-xs leading-relaxed font-medium uppercase">
          A terminal node connection requires explicit acknowledgement of institutional AlphaForge Operating Protocols.
        </p>
      </div>

      <div className="max-h-[350px] lg:max-h-[450px] overflow-y-auto px-6 lg:px-8 py-4 space-y-4 scrollbar-hide border-y border-border-subtle bg-surface/30">
        {terms.map((term) => (
          <div key={term.id} className={cn("p-4 rounded-xl border transition-all", term.bg, term.border)}>
            <div className="flex items-start gap-4">
              <Checkbox 
                id={`term-${term.id}`} 
                checked={agreedTerms[term.id]} 
                onCheckedChange={(v) => onToggleTerm(term.id, v as boolean)} 
                className="mt-1"
              />
              <Label htmlFor={`term-${term.id}`} className="space-y-2 cursor-pointer flex-1">
                <div className={cn("text-[10px] font-black uppercase flex items-center gap-2", term.color)}>
                  <term.icon size={12} />
                  {term.label}
                </div>
                <p className="text-[9px] font-bold text-text-secondary uppercase leading-snug">
                  {term.text}
                </p>
              </Label>
            </div>
          </div>
        ))}
        
        <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 flex items-center gap-4">
          <Checkbox 
            id="term-confirmation" 
            checked={agreedTerms.confirmation} 
            onCheckedChange={(v) => onToggleTerm('confirmation', v as boolean)} 
          />
          <Label htmlFor="term-confirmation" className="text-[10px] font-black text-text-primary uppercase cursor-pointer">
            Authorize Institutional Node Handshake.
          </Label>
        </div>
      </div>
    </div>
  );
}
