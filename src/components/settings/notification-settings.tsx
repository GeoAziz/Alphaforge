'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Bell } from 'lucide-react';
import { useState } from 'react';

const notificationTypes = [
  { id: 'signals', label: 'Signal Alerts', description: 'New trading signals and opportunities' },
  { id: 'trades', label: 'Trade Execution', description: 'Alerts when trades open and close' },
  { id: 'risk', label: 'Risk Warnings', description: 'Critical margin and risk threshold alerts' },
  { id: 'system', label: 'System Updates', description: 'Platform maintenance and updates' },
  { id: 'liquidation', label: 'Liquidation Risk', description: 'Warnings when approaching liquidation' },
  { id: 'performance', label: 'Performance Reports', description: 'Daily/weekly performance summaries' },
];

export function NotificationSettings() {
  const [notifications, setNotifications] = useState<Record<string, boolean>>({
    signals: true,
    trades: true,
    risk: true,
    system: false,
    liquidation: true,
    performance: true,
  });

  const handleToggle = (id: string) => {
    setNotifications(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <SpotlightCard className="p-8">
      <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
        <Bell size={18} className="text-accent" />
        Notification Preferences
      </h3>

      <div className="space-y-3">
        {notificationTypes.map((notif) => (
          <div key={notif.id} className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <Checkbox 
              id={notif.id}
              checked={notifications[notif.id]}
              onCheckedChange={() => handleToggle(notif.id)}
              className="mt-1 mr-3"
            />
            <Label htmlFor={notif.id} className="flex-1 cursor-pointer">
              <div className="font-bold text-text-primary">{notif.label}</div>
              <div className="text-[10px] text-text-muted mt-1">{notif.description}</div>
            </Label>
          </div>
        ))}
      </div>

      <div className="mt-8 pt-6 border-t border-border-subtle">
        <Label className="text-xs font-black uppercase mb-4 block">Notification Channels</Label>
        <div className="space-y-3">
          <div className="flex items-center p-3 rounded-lg bg-elevated/20 border border-border-subtle">
            <Checkbox id="push" defaultChecked className="mr-3" />
            <Label htmlFor="push" className="font-bold text-sm cursor-pointer flex-1">Push Notifications</Label>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-elevated/20 border border-border-subtle">
            <Checkbox id="email" defaultChecked className="mr-3" />
            <Label htmlFor="email" className="font-bold text-sm cursor-pointer flex-1">Email</Label>
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
