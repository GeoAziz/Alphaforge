'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Globe } from 'lucide-react';
import { useState } from 'react';

export function RegulatorySettings() {
  const [jurisdiction, setJurisdiction] = useState('us');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);

  return (
    <SpotlightCard className="p-8">
      <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
        <Globe size={18} className="text-accent" />
        Regulatory Compliance
      </h3>

      <div className="space-y-6">
        <div>
          <Label className="text-xs font-black uppercase mb-3 block">Jurisdiction</Label>
          <Select value={jurisdiction} onValueChange={setJurisdiction}>
            <SelectTrigger className="bg-surface border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-surface border-border">
              <SelectItem value="us">United States</SelectItem>
              <SelectItem value="eu">European Union (GDPR)</SelectItem>
              <SelectItem value="uk">United Kingdom</SelectItem>
              <SelectItem value="ca">Canada</SelectItem>
              <SelectItem value="sg">Singapore</SelectItem>
              <SelectItem value="hk">Hong Kong</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-[10px] text-text-muted mt-2">Select your primary regulatory jurisdiction</p>
        </div>

        <div className="pt-6 border-t border-border-subtle">
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle">
              <div className="text-sm font-black text-text-primary mb-3">Investment Disclaimers</div>
              <div className="text-[10px] text-text-muted space-y-2 mb-4">
                <p>• AlphaForge is not a licensed investment advisor</p>
                <p>• Trading carries substantial risk of loss</p>
                <p>• Past performance does not guarantee future results</p>
                <p>• Cryptocurrency trading is highly volatile and speculative</p>
              </div>
              <div className="flex items-start p-3 rounded-lg bg-surface border border-border-subtle">
                <Checkbox 
                  id="disclaimer" 
                  checked={disclaimerAccepted}
                  onCheckedChange={(checked) => setDisclaimerAccepted(checked === true)}
                  className="mt-1 mr-3"
                />
                <Label htmlFor="disclaimer" className="text-[10px] text-text-muted cursor-pointer">
                  I acknowledge and accept all investment risks and disclaimers
                </Label>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-red/5 border border-red/20">
              <div className="text-[10px] font-bold text-red uppercase mb-2">Compliance Notice</div>
              <div className="text-[10px] text-red/80">
                Depending on your jurisdiction, digital asset trading may be restricted or regulated. It is your responsibility to comply with local laws and regulations.
              </div>
            </div>
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
