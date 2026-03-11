'use client';

import { useState } from 'react';
import { useUser } from '@/firebase';
import { 
  Link2,
  AlertTriangle,
  Bell,
  Shield,
  Lock,
  FileText,
  Scale,
  ShieldAlert
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { ExchangeConnection } from '@/components/settings/exchange-connection';
import { RiskSettings } from '@/components/settings/risk-settings';
import { NotificationSettings } from '@/components/settings/notification-settings';
import { SecuritySettings } from '@/components/settings/security-settings';
import { AuditLogPanel } from '@/components/settings/audit-log-panel';
import { DataPrivacySettings } from '@/components/settings/data-privacy-settings';
import { RegulatorySettings } from '@/components/settings/regulatory-settings';

export default function SettingsPage() {
  const { user } = useUser();

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Lock size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Configuration Restricted</h2>
          <p className="text-sm text-text-muted">Institutional credentials required to access configuration settings.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 max-w-6xl mx-auto animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Configuration Hub</h1>
        <p className="text-text-secondary text-sm">Manage integrations, risk parameters, security, and compliance settings.</p>
      </header>

      <Tabs defaultValue="exchanges" className="space-y-8">
        <div className="scrollbar-hide overflow-x-auto pb-2 border-b border-border-subtle">
          <TabsList className="bg-transparent p-0 h-auto border-none inline-flex w-max gap-8">
            <TabsTrigger value="exchanges" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <Link2 size={16} /> Exchanges
            </TabsTrigger>
            <TabsTrigger value="risk" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <AlertTriangle size={16} /> Risk
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <Bell size={16} /> Alerts
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <Shield size={16} /> Security
            </TabsTrigger>
            <TabsTrigger value="audit" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <FileText size={16} /> Audit
            </TabsTrigger>
            <TabsTrigger value="privacy" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <Lock size={16} /> Privacy
            </TabsTrigger>
            <TabsTrigger value="compliance" className="gap-2 px-0 pb-3 font-bold uppercase text-[10px] border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent text-text-muted data-[state=active]:text-primary rounded-none transition-all">
              <Scale size={16} /> Compliance
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="exchanges" className="animate-in fade-in duration-300">
          <ExchangeConnection />
        </TabsContent>

        <TabsContent value="risk" className="animate-in fade-in duration-300">
          <RiskSettings />
        </TabsContent>

        <TabsContent value="notifications" className="animate-in fade-in duration-300">
          <NotificationSettings />
        </TabsContent>

        <TabsContent value="security" className="animate-in fade-in duration-300">
          <SecuritySettings />
        </TabsContent>

        <TabsContent value="audit" className="animate-in fade-in duration-300">
          <AuditLogPanel />
        </TabsContent>

        <TabsContent value="privacy" className="animate-in fade-in duration-300">
          <DataPrivacySettings />
        </TabsContent>

        <TabsContent value="compliance" className="animate-in fade-in duration-300">
          <RegulatorySettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
