'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Globe, Scale, ShieldAlert, FileText, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export function RegulatorySettings() {
  const [jurisdiction, setJurisdiction] = useState('uk');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(true);

  const notices: Record<string, { title: string, text: string, link: string }> = {
    uk: {
      title: "FCA Algorithmic Trading Notice",
      text: "AlphaForge provides market commentary and technological tools. Under FCA DP16/6, automated copy trading directed by the user is not considered discretionary management.",
      link: "https://www.fca.org.uk"
    },
    us: {
      title: "SEC/CFTC Compliance Node",
      text: "Institutional signals are for informational purposes only. Automated execution may require registration as a Commodity Trading Adviser (CTA) for US persons.",
      link: "https://www.sec.gov"
    },
    eu: {
      title: "MiFID II Intelligence Notice",
      text: "This node operates under ESMA information service frameworks. All data processing is strictly GDPR compliant under local authority supervision.",
      link: "https://www.esma.europa.eu"
    }
  };

  const activeNotice = notices[jurisdiction] || notices.uk;

  return (
    <div className="space-y-8 max-w-4xl mx-auto animate-page">
      <SpotlightCard className="p-8 space-y-10">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-xl font-black uppercase tracking-tight flex items-center gap-2 text-text-primary">
              <Scale size={24} className="text-primary" />
              Compliance Protocol
            </h3>
            <p className="text-xs text-text-muted font-bold uppercase tracking-widest">Authorized node jurisdiction & licensing status</p>
          </div>
          <Badge variant="outline" className="border-green/20 text-green uppercase font-black text-[10px]">Audit Passed</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="space-y-6">
            <div className="space-y-3">
              <Label className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                <Globe size={14} /> Active Jurisdiction
              </Label>
              <Select value={jurisdiction} onValueChange={setJurisdiction}>
                <SelectTrigger className="h-12 bg-elevated/30 border-border-subtle font-black uppercase text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="glass border-border-subtle">
                  <SelectItem value="uk" className="text-xs font-bold uppercase">United Kingdom (FCA)</SelectItem>
                  <SelectItem value="us" className="text-xs font-bold uppercase">United States (SEC/CFTC)</SelectItem>
                  <SelectItem value="eu" className="text-xs font-bold uppercase">European Union (ESMA)</SelectItem>
                  <SelectItem value="sg" className="text-xs font-bold uppercase">Singapore (MAS)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="p-6 rounded-2xl bg-amber/5 border border-amber/20 space-y-4 animate-in slide-in-from-left-4 duration-500">
              <div className="flex items-center gap-2 text-amber">
                <ShieldAlert size={16} />
                <h4 className="text-xs font-black uppercase tracking-tight">{activeNotice.title}</h4>
              </div>
              <p className="text-[10px] text-text-secondary leading-relaxed font-medium uppercase">
                {activeNotice.text}
              </p>
              <Button variant="link" className="p-0 h-auto text-[9px] font-black uppercase text-amber hover:text-amber/80 flex items-center gap-1">
                View Regulator Policy <ExternalLink size={10} />
              </Button>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <Label className="text-[10px] font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                <FileText size={14} /> Transparency Proof
              </Label>
              <div className="space-y-3">
                {[
                  { label: "Terms of Handshake", version: "v2.4.1" },
                  { label: "Privacy Sovereignty", version: "v1.0.8" },
                  { label: "Execution Risk Disclosure", version: "v3.2.0" }
                ].map(doc => (
                  <div key={doc.label} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between hover:bg-elevated/40 transition-all group cursor-pointer">
                    <span className="text-[10px] font-black uppercase text-text-secondary group-hover:text-primary transition-colors">{doc.label}</span>
                    <span className="text-[9px] font-mono font-bold text-text-muted">{doc.version}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-border-subtle">
          <div className={cn(
            "p-6 rounded-2xl border flex items-center gap-6",
            disclaimerAccepted ? "bg-green/5 border-green/20" : "bg-red/5 border-red/20"
          )}>
            <Checkbox 
              id="master-disclaimer" 
              checked={disclaimerAccepted}
              onCheckedChange={(v) => setDisclaimerAccepted(v === true)}
              className="w-6 h-6 rounded-lg border-2"
            />
            <Label htmlFor="master-disclaimer" className="space-y-1 cursor-pointer">
              <div className="text-xs font-black uppercase text-text-primary">Global Institutional Disclaimer Acknowledgement</div>
              <p className="text-[10px] text-text-muted font-bold uppercase leading-relaxed">
                I acknowledge that AlphaForge operates as a technology node provider and all algorithmic signals are for informational purposes only.
              </p>
            </Label>
          </div>
        </div>
      </SpotlightCard>
    </div>
  );
}
