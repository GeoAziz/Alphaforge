'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Shield, Smartphone, LogOut } from 'lucide-react';
import { useState } from 'react';

export function SecuritySettings() {
  const [is2faEnabled, setIs2faEnabled] = useState(true);
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const activeSessions = [
    { device: 'Chrome on macOS', ip: '192.168.1.1', lastActive: '2m ago' },
    { device: 'Safari on iPhone', ip: '10.0.0.5', lastActive: '1h ago' },
  ];

  return (
    <div className="space-y-6">
      <SpotlightCard className="p-8">
        <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
          <Shield size={18} className="text-primary" />
          Two-Factor Authentication
        </h3>

        <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Smartphone size={18} className="text-primary" />
            <div>
              <div className="font-bold text-text-primary text-sm">Authenticator App</div>
              <div className="text-[10px] text-text-muted">TOTP-based verification</div>
            </div>
          </div>
          <Badge className={is2faEnabled ? "bg-green/10 text-green border-green/20" : "bg-amber/10 text-amber border-amber/20"}>
            {is2faEnabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>

        <p className="text-[10px] text-text-muted mt-4">We strongly recommend keeping 2FA enabled for account security.</p>
      </SpotlightCard>

      <SpotlightCard className="p-8">
        <h3 className="text-lg font-black uppercase tracking-tight text-text-primary mb-6">Change Password</h3>

        {showPasswordForm ? (
          <div className="space-y-4">
            <div>
              <Label className="text-xs font-black uppercase">Current Password</Label>
              <Input type="password" placeholder="••••••••" className="mt-2" />
            </div>
            <div>
              <Label className="text-xs font-black uppercase">New Password</Label>
              <Input type="password" placeholder="••••••••" className="mt-2" />
            </div>
            <div>
              <Label className="text-xs font-black uppercase">Confirm Password</Label>
              <Input type="password" placeholder="••••••••" className="mt-2" />
            </div>
            <div className="flex gap-2">
              <Button className="flex-1 bg-primary text-primary-foreground font-black">Update Password</Button>
              <Button variant="outline" className="flex-1" onClick={() => setShowPasswordForm(false)}>Cancel</Button>
            </div>
          </div>
        ) : (
          <Button 
            onClick={() => setShowPasswordForm(true)}
            className="w-full bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 font-black uppercase"
          >
            Change Password
          </Button>
        )}
      </SpotlightCard>

      <SpotlightCard className="p-8">
        <h3 className="text-lg font-black uppercase tracking-tight text-text-primary mb-6">Active Sessions</h3>

        <div className="space-y-3">
          {activeSessions.map((session, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between">
              <div>
                <div className="font-bold text-text-primary text-sm">{session.device}</div>
                <div className="text-[10px] text-text-muted">IP: {session.ip} • Last active {session.lastActive}</div>
              </div>
              <Button variant="ghost" size="sm" className="text-red hover:text-red">
                <LogOut size={16} />
              </Button>
            </div>
          ))}
        </div>
      </SpotlightCard>
    </div>
  );
}
