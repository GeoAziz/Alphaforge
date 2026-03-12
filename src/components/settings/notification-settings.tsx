'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Bell, Send, MessageSquare, Mail, Smartphone, Info, ShieldCheck, QrCode, Terminal } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const notificationTypes = [
  { id: 'signals', label: 'Signal Alpha Alerts', description: 'New high-confidence institutional trading signals.' },
  { id: 'trades', label: 'Execution confirmations', description: 'Real-time telemetry for all opened and resolved nodes.' },
  { id: 'risk', label: 'Margin & Risk Warnings', description: 'Critical portfolio exposure and liquidation thresholds.' },
  { id: 'system', label: 'System Integrity', description: 'Model retrains, node updates, and infrastructure alerts.' },
];

export function NotificationSettings() {
  const [notifications, setNotifications] = useState<Record<string, boolean>>({
    signals: true,
    trades: true,
    risk: true,
    system: false,
  });

  const [activeChannels, setActiveChannels] = useState<Record<string, boolean>>({
    push: true,
    email: true,
    telegram: false,
    discord: false
  });

  const handleToggle = (id: string) => {
    setNotifications(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-6xl mx-auto">
      {/* Type Filters */}
      <SpotlightCard className="p-8 lg:col-span-7 space-y-8">
        <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary">
          <Bell size={18} className="text-primary" />
          Intelligence Routing
        </h3>

        <div className="space-y-4">
          {notificationTypes.map((notif) => (
            <div 
              key={notif.id} 
              onClick={() => handleToggle(notif.id)}
              className={cn(
                "flex items-start p-5 rounded-2xl border transition-all cursor-pointer group",
                notifications[notif.id] ? "bg-primary/5 border-primary/20 shadow-[0_0_20px_rgba(96,165,250,0.05)]" : "bg-elevated/10 border-border-subtle hover:bg-elevated/30"
              )}
            >
              <Checkbox 
                id={notif.id}
                checked={notifications[notif.id]}
                onCheckedChange={() => handleToggle(notif.id)}
                className="mt-1 mr-4 border-border-subtle"
              />
              <Label htmlFor={notif.id} className="flex-1 cursor-pointer space-y-1">
                <div className="font-black text-sm uppercase tracking-tight text-text-primary group-hover:text-primary transition-colors">{notif.label}</div>
                <div className="text-[10px] text-text-muted font-bold uppercase leading-relaxed">{notif.description}</div>
              </Label>
            </div>
          ))}
        </div>
      </SpotlightCard>

      {/* Channel Connections */}
      <div className="lg:col-span-5 space-y-8">
        <SpotlightCard className="p-8 space-y-8">
          <h3 className="text-sm font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
            <Terminal size={16} className="text-primary" />
            Communication Clusters
          </h3>

          <div className="space-y-6">
            {/* Telegram Channel */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 border border-blue-500/20">
                    <Send size={20} />
                  </div>
                  <span className="text-[11px] font-black uppercase tracking-widest">Telegram Node</span>
                </div>
                <Switch 
                  checked={activeChannels.telegram} 
                  onCheckedChange={(v) => setActiveChannels(prev => ({...prev, telegram: v}))} 
                />
              </div>
              
              {activeChannels.telegram && (
                <div className="p-6 rounded-2xl bg-inset border border-border-subtle flex flex-col items-center gap-6 animate-in zoom-in-95 duration-300">
                  <div className="w-32 h-32 bg-white rounded-xl flex items-center justify-center shadow-2xl">
                    <QrCode size={100} className="text-black" />
                  </div>
                  <div className="text-center space-y-2">
                    <div className="text-[10px] font-black uppercase text-text-primary">Establish Bot Handshake</div>
                    <p className="text-[9px] text-text-muted font-bold uppercase leading-relaxed max-w-[200px]">
                      Scan with Telegram to authorize AlphaForge Intelligence Core.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <Separator className="bg-border-subtle" />

            {/* Discord Channel */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                    <MessageSquare size={20} />
                  </div>
                  <span className="text-[11px] font-black uppercase tracking-widest">Discord Bridge</span>
                </div>
                <Switch 
                  checked={activeChannels.discord} 
                  onCheckedChange={(v) => setActiveChannels(prev => ({...prev, discord: v}))} 
                />
              </div>

              {activeChannels.discord && (
                <div className="space-y-3 animate-in slide-in-from-top-4">
                  <Label className="text-[9px] font-black uppercase text-text-muted tracking-widest">Webhook Payload Endpoint</Label>
                  <div className="flex gap-2">
                    <Input placeholder="https://discord.com/api/webhooks/..." className="h-10 bg-elevated/30 border-border-subtle text-[10px] font-mono" />
                    <Button className="h-10 bg-primary text-primary-foreground font-black uppercase text-[9px] px-4">Test</Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </SpotlightCard>

        <div className="p-6 rounded-3xl bg-primary/5 border border-primary/10 flex items-start gap-4">
          <ShieldCheck size={20} className="text-primary mt-1 shrink-0" />
          <div className="space-y-1">
            <div className="text-[10px] font-black uppercase text-text-primary">Encrypted Routing</div>
            <p className="text-[9px] font-bold text-text-muted uppercase leading-relaxed">
              All intelligence routing is end-to-end encrypted. AlphaForge does not store plain-text alert payloads.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
