'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Bell } from 'lucide-react';

interface StepNotificationsProps {
  prefs: Record<string, boolean>;
  onChange: (key: string, value: boolean) => void;
}

export function StepNotifications({ prefs, onChange }: StepNotificationsProps) {
  const notifications = [
    { id: 'signals', label: 'Signal Alerts', description: 'New trading signals and opportunities' },
    { id: 'trades', label: 'Trade Execution', description: 'Alerts when trades open and close' },
    { id: 'risk', label: 'Risk Warnings', description: 'Critical margin and risk threshold alerts' },
    { id: 'system', label: 'System Updates', description: 'Platform maintenance and updates' },
  ];

  return (
    <SpotlightCard className="p-8 max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <Bell size={24} className="text-accent" />
        <h2 className="text-2xl font-black uppercase tracking-tight">Notification Preferences</h2>
      </div>

      <p className="text-text-secondary text-sm mb-8">Choose which alerts you'd like to receive:</p>

      <div className="space-y-4">
        {notifications.map((notif) => (
          <div key={notif.id} className="flex items-start p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <Checkbox 
              id={notif.id}
              checked={prefs[notif.id] || false}
              onCheckedChange={(checked) => onChange(notif.id, checked === true)}
              className="mt-1 mr-3"
            />
            <Label htmlFor={notif.id} className="flex-1 cursor-pointer">
              <div className="font-bold text-text-primary">{notif.label}</div>
              <div className="text-[10px] text-text-muted mt-1">{notif.description}</div>
            </Label>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
