'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { AlertTriangle } from 'lucide-react';

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
  return (
    <SpotlightCard className="p-8 max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <AlertTriangle size={24} className="text-red" />
        <h2 className="text-2xl font-black uppercase tracking-tight">Regulatory & Compliance</h2>
      </div>

      <p className="text-text-secondary text-sm mb-8">Please acknowledge the following compliance requirements (required to proceed):</p>

      <div className="space-y-4 mb-8">
        <div className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle">
          <Checkbox 
            id="gdpr" 
            checked={gdprAccepted}
            onCheckedChange={onGdprChange}
            className="mt-1 mr-3"
          />
          <Label htmlFor="gdpr" className="flex-1 cursor-pointer">
            <div className="font-bold text-text-primary">GDPR Compliance</div>
            <div className="text-[10px] text-text-muted mt-1">I consent to AlphaForge processing my personal data under GDPR regulations</div>
          </Label>
        </div>

        <div className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle">
          <Checkbox 
            id="ccpa"
            checked={ccpaAccepted}
            onCheckedChange={onCcpaChange}
            className="mt-1 mr-3"
          />
          <Label htmlFor="ccpa" className="flex-1 cursor-pointer">
            <div className="font-bold text-text-primary">CCPA Rights (US Only)</div>
            <div className="text-[10px] text-text-muted mt-1">I acknowledge my rights under the California Consumer Privacy Act, if applicable</div>
          </Label>
        </div>

        <div className="flex items-start p-4 rounded-xl bg-red/5 border border-red/20">
          <Checkbox 
            id="disclaimer"
            checked={disclaimerAccepted}
            onCheckedChange={onDisclaimerChange}
            className="mt-1 mr-3"
          />
          <Label htmlFor="disclaimer" className="flex-1 cursor-pointer">
            <div className="font-bold text-red">Investment Risk Acknowledgment</div>
            <div className="space-y-1 text-[10px] text-red/80 mt-1">
              <p>• AlphaForge is not a licensed investment advisor</p>
              <p>• I understand that cryptocurrency trading carries substantial risk of loss</p>
              <p>• Past performance does not guarantee future results</p>
              <p>• I am financially capable of bearing the risk of total loss</p>
            </div>
          </Label>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-amber/5 border border-amber/20">
        <div className="text-[10px] font-bold text-amber uppercase mb-2">⚠ Important</div>
        <div className="text-[10px] text-amber/80">
          You must accept all three requirements above to proceed. This step cannot be skipped. These requirements are binding and will be recorded in your account audit trail.
        </div>
      </div>
    </SpotlightCard>
  );
}
