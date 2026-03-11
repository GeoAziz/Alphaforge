'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Lock } from 'lucide-react';

export function DataPrivacySettings() {
  return (
    <div className="space-y-6">
      <SpotlightCard className="p-8">
        <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
          <Lock size={18} className="text-primary" />
          Data Privacy Controls
        </h3>

        <div className="space-y-4 mb-8">
          <div className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle">
            <Checkbox id="gdpr" defaultChecked className="mt-1 mr-3" />
            <Label htmlFor="gdpr" className="flex-1 cursor-pointer">
              <div className="font-bold text-text-primary">GDPR Compliance</div>
              <div className="text-[10px] text-text-muted mt-1">I consent to AlphaForge processing my personal data under GDPR regulations</div>
            </Label>
          </div>

          <div className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle">
            <Checkbox id="ccpa" className="mt-1 mr-3" />
            <Label htmlFor="ccpa" className="flex-1 cursor-pointer">
              <div className="font-bold text-text-primary">CCPA Rights</div>
              <div className="text-[10px] text-text-muted mt-1">I acknowledge my rights under California Consumer Privacy Act</div>
            </Label>
          </div>
        </div>

        <div className="pt-6 border-t border-border-subtle">
          <Label className="text-xs font-black uppercase mb-4  block">Data Management</Label>
          <div className="space-y-3">
            <Button className="w-full bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 font-black justify-start">
              ↓ Download My Data
            </Button>
            <Button className="w-full bg-amber/10 text-amber border border-amber/20 hover:bg-amber/20 font-black justify-start">
              🔄 Request Data Export
            </Button>
            <Button className="w-full bg-red/10 text-red border border-red/20 hover:bg-red/20 font-black justify-start">
              🗑 Request Account Deletion
            </Button>
          </div>
        </div>

        <div className="mt-6 p-4 rounded-lg bg-amber/5 border border-amber/20">
          <div className="text-[10px] font-bold text-amber uppercase">Important</div>
          <div className="text-xs text-amber/80 mt-2">Account deletion is permanent and cannot be undone. All data will be securely purged within 30 days.</div>
        </div>
      </SpotlightCard>
    </div>
  );
}
