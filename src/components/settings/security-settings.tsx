'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Shield, Smartphone, LogOut, Key, Fingerprint, Globe, Laptop, SmartphoneIcon } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export function SecuritySettings() {
  const [is2faEnabled, setIs2faEnabled] = useState(true);
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const activeSessions = [
    { device: 'Workstation Terminal', os: 'Chrome on macOS', ip: '192.168.1.1', lastActive: 'Active Now', current: true },
    { device: 'Mobile Node', os: 'Safari on iOS', ip: '10.0.0.5', lastActive: '1h ago', current: false },
  ];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Institutional 2FA */}
        <SpotlightCard className="p-8 space-y-8 border-primary/10">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
              <Smartphone size={24} />
            </div>
            <Switch checked={is2faEnabled} onCheckedChange={setIs2faEnabled} />
          </div>
          
          <div className="space-y-2">
            <h3 className="text-xl font-black uppercase tracking-tight">Institutional 2FA</h3>
            <p className="text-xs text-text-muted leading-relaxed uppercase font-bold">Require a cryptographic handshake from your mobile node for all authorized executions and API rotations.</p>
          </div>

          <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Fingerprint size={18} className="text-primary" />
              <span className="text-[10px] font-black uppercase text-text-primary">Google Authenticator</span>
            </div>
            <Badge className="bg-green/10 text-green border-green/20 h-5 px-2 text-[8px] font-black uppercase">Active</Badge>
          </div>
        </SpotlightCard>

        {/* Change Credentials */}
        <SpotlightCard className="p-8 space-y-8 border-border-subtle">
          <div className="w-12 h-12 rounded-xl bg-elevated flex items-center justify-center text-text-muted border border-border-subtle">
            <Key size={24} />
          </div>
          
          <div className="space-y-2">
            <h3 className="text-xl font-black uppercase tracking-tight">Credential Rotation</h3>
            <p className="text-xs text-text-muted leading-relaxed uppercase font-bold">Rotate institutional node credentials to invalidate previous session handshakes.</p>
          </div>

          {showPasswordForm ? (
            <div className="space-y-4 animate-in slide-in-from-top-4">
              <Input type="password" placeholder="Current Secret" className="h-12 bg-elevated/30 border-border-subtle font-mono text-xs" />
              <Input type="password" placeholder="New Node Secret" className="h-12 bg-elevated/30 border-border-subtle font-mono text-xs" />
              <div className="flex gap-2">
                <Button className="flex-1 bg-primary text-primary-foreground font-black uppercase text-[10px]">Update Node</Button>
                <Button variant="ghost" onClick={() => setShowPasswordForm(false)} className="text-[10px] font-black uppercase px-4">Cancel</Button>
              </div>
            </div>
          ) : (
            <Button 
              onClick={() => setShowPasswordForm(true)}
              variant="outline"
              className="w-full h-12 border-border-subtle font-black uppercase text-[10px] tracking-widest hover:bg-elevated"
            >
              Initialize Rotation
            </Button>
          )}
        </SpotlightCard>
      </div>

      {/* Active Session Clusters */}
      <SpotlightCard className="p-8">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
            <Globe size={16} className="text-primary" />
            Active Session Clusters
          </h3>
          <Button variant="ghost" className="text-red text-[10px] font-black uppercase h-8 hover:bg-red/5">Terminate All Other Nodes</Button>
        </div>

        <div className="space-y-4">
          {activeSessions.map((session, idx) => (
            <div key={idx} className={cn(
              "p-5 rounded-2xl border flex items-center justify-between transition-all",
              session.current ? "bg-primary/5 border-primary/20" : "bg-elevated/10 border-border-subtle"
            )}>
              <div className="flex items-center gap-5">
                <div className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center border",
                  session.current ? "bg-primary/10 text-primary border-primary/20" : "bg-elevated text-text-muted border-border-subtle"
                )}>
                  {session.os.includes('iOS') ? <SmartphoneIcon size={20} /> : <Laptop size={20} />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-black uppercase tracking-tight">{session.device}</span>
                    {session.current && <Badge className="bg-primary text-primary-foreground h-4 px-1.5 text-[8px] font-black uppercase">Current Node</Badge>}
                  </div>
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest mt-1">
                    {session.os} • IP: {session.ip}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-black uppercase text-text-muted mb-2">{session.lastActive}</div>
                {!session.current && (
                  <Button variant="ghost" size="sm" className="h-8 w-8 text-red hover:text-red hover:bg-red/5 rounded-lg">
                    <LogOut size={16} />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </SpotlightCard>
    </div>
  );
}
