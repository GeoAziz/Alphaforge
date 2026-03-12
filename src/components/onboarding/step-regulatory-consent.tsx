'use client';

import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { ShieldAlert, Scale, ScrollText, Lock, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useRef, useEffect, useState } from 'react';

interface StepRegulatoryConsentProps {
  gdprAccepted: boolean;
  ccpaAccepted: boolean;
  disclaimerAccepted: boolean;
  onGdprChange: (checked: boolean) => void;
  onCcpaChange: (checked: boolean) => void;
  onDisclaimerChange: (checked: boolean) => void;
}

export function StepRegulatoryConsent({
  gdprAccepted,
  ccpaAccepted,
  disclaimerAccepted,
  onGdprChange,
  onCcpaChange,
  onDisclaimerChange,
}: StepRegulatoryConsentProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      const isBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 10;
      if (isBottom) setHasScrolledToBottom(true);
    };

    el.addEventListener('scroll', handleScroll);
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="space-y-4">
        <div className="w-12 h-12 rounded-xl bg-red/10 flex items-center justify-center text-red border border-red/20 mb-6 shadow-inner">
          <Scale size={24} />
        </div>
        <h2 className="text-2xl font-black uppercase tracking-tight">Regulatory Handshake</h2>
        <p className="text-sm text-text-muted leading-relaxed uppercase font-bold text-[10px] tracking-widest">
          A terminal handshake requires explicit acknowledgement of institutional risk and data sovereignty protocols.
        </p>
      </div>

      <div 
        ref={scrollRef}
        className="max-h-[300px] overflow-y-auto p-6 rounded-2xl bg-elevated/20 border border-border-subtle scrollbar-hide space-y-6"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-red">
            <ShieldAlert size={16} />
            <h3 className="text-xs font-black uppercase tracking-widest">CRITICAL RISK DISCLOSURE</h3>
          </div>
          <div className="text-[10px] text-text-secondary leading-relaxed space-y-3 font-medium uppercase">
            <p>1. TRADING CRYPTOCURRENCY AND DERIVATIVES INVOLVES SUBSTANTIAL RISK OF TOTAL CAPITAL LOSS. ALPHAFORGE IS A TECHNOLOGY PROVIDER, NOT A REGULATED INVESTMENT ADVISER.</p>
            <p>2. ALGORITHMIC MODELS CAN FAIL WITHOUT WARNING. PAST PERFORMANCE (BACKTEST OR PAPER) IS NO GUARANTEE OF FUTURE ALPHA OR EXECUTION PARITY.</p>
            <p>3. LIQUIDATION RISK: TRADING PERPETUALS WITH LEVERAGE CAN RESULT IN TOTAL ACCOUNT WIPE-OUT IN SUB-SECOND TIME HORIZONS DURING VOLATILITY EVENTS.</p>
            <p>4. TECHNOLOGY RISK: NETWORK LATENCY, EXCHANGE API DOWNTIME, OR NODE INTERRUPTIONS MAY PREVENT STOP-LOSS EXECUTION.</p>
          </div>
        </div>

        <div className="space-y-4 border-t border-border-subtle pt-6">
          <div className="flex items-center gap-2 text-primary">
            <Lock size={16} />
            <h3 className="text-xs font-black uppercase tracking-widest">DATA SOVEREIGNTY</h3>
          </div>
          <div className="text-[10px] text-text-secondary leading-relaxed space-y-3 font-medium uppercase">
            <p>YOUR EXCHANGE API KEYS ARE ENCRYPTED VIA AES-256 ENVELOPE ENCRYPTION. ALPHAFORGE EMPLOYS ZERO-KNOWLEDGE PRINCIPLES; WITHDRAWAL PERMISSIONS ARE STRICTLY PROHIBITED.</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className={cn(
          "flex items-start p-4 rounded-xl border transition-all",
          gdprAccepted ? "bg-primary/5 border-primary/20" : "bg-elevated/20 border-border-subtle"
        )}>
          <Checkbox 
            id="gdpr" 
            checked={gdprAccepted}
            onCheckedChange={(v) => onGdprChange(v === true)}
            className="mt-1 mr-3"
          />
          <Label htmlFor="gdpr" className="flex-1 cursor-pointer">
            <div className="font-black text-[10px] text-text-primary uppercase tracking-tight">GDPR / CCPA Node Handshake</div>
            <div className="text-[9px] text-text-muted mt-1 uppercase font-bold">I authorize data processing for terminal synchronization</div>
          </Label>
        </div>

        <div className={cn(
          "flex items-start p-4 rounded-xl border transition-all",
          ccpaAccepted ? "bg-primary/5 border-primary/20" : "bg-elevated/20 border-border-subtle"
        )}>
          <Checkbox 
            id="ccpa"
            checked={ccpaAccepted}
            onCheckedChange={(v) => onCcpaChange(v === true)}
            className="mt-1 mr-3"
          />
          <Label htmlFor="ccpa" className="flex-1 cursor-pointer">
            <div className="font-black text-[10px] text-text-primary uppercase tracking-tight">Institutional Handshake</div>
            <div className="text-[9px] text-text-muted mt-1 uppercase font-bold">I am an authorized entity and not a US-sanctioned person</div>
          </Label>
        </div>

        <div className={cn(
          "flex items-start p-4 rounded-xl border transition-all",
          disclaimerAccepted ? "bg-red/10 border-red/30" : "bg-red/5 border-red/10"
        )}>
          <Checkbox 
            id="disclaimer"
            checked={disclaimerAccepted}
            onCheckedChange={(v) => onDisclaimerChange(v === true)}
            disabled={!hasScrolledToBottom}
            className="mt-1 mr-3"
          />
          <Label htmlFor="disclaimer" className={cn(
            "flex-1 cursor-pointer",
            !hasScrolledToBottom && "opacity-50 cursor-not-allowed"
          )}>
            <div className="font-black text-[10px] text-red uppercase tracking-tight">Risk Acknowledgement</div>
            <div className="text-[9px] text-red/80 mt-1 uppercase font-bold">
              {hasScrolledToBottom ? "I have read and accept all risk disclosures" : "Scroll disclosure to acknowledge"}
            </div>
          </Label>
        </div>
      </div>
    </div>
  );
}
