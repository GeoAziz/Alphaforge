'use client';

import { useState } from 'react';
import { useFirestore, useUser, useDoc, useCollection, useMemoFirebase } from '@/firebase';
import { doc, collection, orderBy, limit } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { UserProfile, ConnectedExchange } from '@/lib/types';
import { 
  User, 
  Shield, 
  Key, 
  Globe, 
  CreditCard, 
  Plus, 
  Trash2, 
  Loader2,
  Bell,
  Sliders,
  FileText,
  Lock,
  Scale,
  Database,
  ShieldAlert,
  ArrowRight,
  Info
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";

export default function SettingsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [isSaving, setIsSaving] = useState(false);
  const [activeStep, setActiveStep] = useState(1);

  const profileRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid);
  }, [user, db]);

  const exchangesQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return collection(db, 'users', user.uid, 'connectedExchanges');
  }, [user, db]);

  const { data: profile } = useDoc<UserProfile>(profileRef);
  const { data: exchanges } = useCollection<ConnectedExchange>(exchangesQuery);

  function handleUpdateProfile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!profileRef) return;
    setIsSaving(true);
    
    const formData = new FormData(e.currentTarget);
    const updates = {
      name: formData.get('name') as string,
      riskTolerance: formData.get('riskTolerance') as string,
      onboardingComplete: true
    };

    setDocumentNonBlocking(profileRef, updates, { merge: true });
    
    setTimeout(() => setIsSaving(false), 800);
  }

  const mockAuditLogs = [
    { id: 1, action: 'API Connection Established', target: 'Binance API 01', timestamp: '2024-03-01 12:42:15', status: 'Success' },
    { id: 2, action: 'Global Risk Calibrated', target: 'Risk Engine', timestamp: '2024-02-28 09:15:02', status: 'Success' },
    { id: 3, action: '2FA Validation', target: 'Security Protocol', timestamp: '2024-02-28 09:14:45', status: 'Authorized' },
    { id: 4, action: 'Node Session Initiated', target: 'Terminal AF-01', timestamp: '2024-02-28 09:14:30', status: 'Success' },
  ];

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Lock size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Configuration Restricted</h2>
          <p className="text-sm text-text-muted">Institutional credentials required to access terminal security nodes and API synchronization clusters.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-24 max-w-7xl mx-auto">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Terminal Control Center</h1>
        <p className="text-muted-foreground text-sm">Configure global risk parameters, security protocols, and institutional API connectivity.</p>
      </header>

      <Tabs defaultValue="profile" className="space-y-8">
        <div className="scrollbar-hide overflow-x-auto pb-2">
          <TabsList className="bg-elevated/50 p-1 rounded-xl border border-border-subtle h-12 inline-flex w-max">
            <TabsTrigger value="profile" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <User size={14} /> Profile
            </TabsTrigger>
            <TabsTrigger value="exchanges" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Globe size={14} /> Connectivity
            </TabsTrigger>
            <TabsTrigger value="risk" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Sliders size={14} /> Risk
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Key size={14} /> Security
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Bell size={14} /> Alerts
            </TabsTrigger>
            <TabsTrigger value="audit" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <FileText size={14} /> Audit Log
            </TabsTrigger>
            <TabsTrigger value="legal" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Scale size={14} /> Compliance
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Profile Tab */}
        <TabsContent value="profile" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <SpotlightCard className="col-span-12 lg:col-span-7 p-8">
              <form onSubmit={handleUpdateProfile} className="space-y-8">
                <div className="space-y-6">
                  <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                    <User size={16} className="text-primary" /> Identity Handshake
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label className="text-[10px] font-black uppercase text-text-muted">Institutional Identity</Label>
                      <Input name="name" defaultValue={profile?.name || ''} className="bg-elevated/30 border-border-subtle h-12 font-bold" />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[10px] font-black uppercase text-text-muted">Primary Node Email</Label>
                      <Input disabled value={user.email || 'Anonymous Guest Session'} className="bg-elevated/10 border-border-subtle h-12 opacity-50 font-mono" />
                    </div>
                  </div>
                </div>

                <div className="space-y-6 pt-8 border-t border-border-subtle">
                  <h3 className="text-sm font-black uppercase text-text-muted">Subscription Cluster</h3>
                  <div className="p-6 rounded-2xl bg-primary/5 border border-primary/10 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center text-primary border border-primary/30">
                        <Shield size={24} />
                      </div>
                      <div>
                        <div className="text-lg font-black uppercase tracking-tight">Alpha {profile?.plan || 'Free'} Core</div>
                        <p className="text-[10px] text-text-muted font-bold uppercase">Institutional grade signals & latency</p>
                      </div>
                    </div>
                    <Button variant="outline" className="border-primary/50 text-primary hover:bg-primary/10 font-black uppercase text-[10px] h-10 px-6 rounded-xl">
                      Upgrade Node
                    </Button>
                  </div>
                </div>

                <Button type="submit" disabled={isSaving} className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-3 rounded-2xl shadow-[0_0_25px_rgba(96,165,250,0.3)]">
                  {isSaving ? <Loader2 className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
                  Synchronize Terminal Identity
                </Button>
              </form>
            </SpotlightCard>

            <div className="col-span-12 lg:col-span-5 space-y-6">
              <SpotlightCard variant="accent" className="p-8">
                <h3 className="text-xs font-black uppercase tracking-widest text-primary mb-6">Session Telemetry</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase">Connection Status</span>
                    <Badge className="bg-green/20 text-green border-green/30 uppercase text-[9px] font-black">Live & Synced</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase">Terminal Cluster</span>
                    <span className="text-[10px] font-mono font-black">AF-NODE-US-01</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase">API Latency</span>
                    <span className="text-[10px] font-mono font-black text-primary">14.2 ms</span>
                  </div>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Connectivity Tab */}
        <TabsContent value="exchanges" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-8 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                  <Globe size={16} className="text-primary" /> Active API Handshakes
                </h3>
                <Button size="sm" className="bg-primary h-10 px-6 text-[10px] font-black uppercase gap-2 rounded-xl shadow-lg">
                  <Plus size={14} /> Connect New API
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exchanges?.map(ex => (
                  <SpotlightCard key={ex.id} className="p-6 border-primary/5 hover:border-primary/20 transition-all">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-elevated flex items-center justify-center font-black text-xl border border-border-subtle shadow-inner">
                          {ex.exchange[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="font-black capitalize text-lg">{ex.exchange}</div>
                          <div className="text-[9px] text-text-muted font-bold uppercase font-mono tracking-tighter">ID: {ex.id.slice(0, 12)}...</div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge className="bg-green/10 text-green border-green/20 uppercase text-[9px] font-black">Encrypted</Badge>
                        <span className="text-[8px] font-bold text-text-muted uppercase">Synced: 12m ago</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mb-6">
                      <div className="p-2 rounded-lg bg-elevated/30 border border-border-subtle">
                        <div className="text-[8px] font-black text-text-muted uppercase">Permissions</div>
                        <div className="text-[10px] font-bold">READ / TRADE</div>
                      </div>
                      <div className="p-2 rounded-lg bg-elevated/30 border border-border-subtle">
                        <div className="text-[8px] font-black text-text-muted uppercase">Latency</div>
                        <div className="text-[10px] font-bold text-primary">8.2 ms</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" className="flex-1 h-9 text-[9px] font-black uppercase text-red hover:bg-red/10 rounded-lg">
                        <Trash2 size={12} className="mr-2" /> Terminate Connection
                      </Button>
                    </div>
                  </SpotlightCard>
                ))}

                {(!exchanges || exchanges.length === 0) && (
                  <div className="col-span-2 h-60 flex flex-col items-center justify-center border border-dashed border-border-subtle rounded-3xl bg-surface/30 text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-elevated flex items-center justify-center text-text-muted">
                      <Database size={32} />
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm font-black uppercase tracking-tight">No active API handshakes detected</div>
                      <p className="text-[10px] text-text-muted font-bold uppercase">Initialize a connection to enable algorithmic trading nodes.</p>
                    </div>
                    <Button variant="outline" className="border-primary/30 text-primary uppercase text-[10px] font-black h-10 px-8 rounded-xl">
                      Begin Connectivity Flow
                    </Button>
                  </div>
                )}
              </div>
            </div>

            <div className="col-span-12 lg:col-span-4">
              <SpotlightCard className="p-8 border-amber/10 bg-amber/5 h-full">
                <div className="space-y-6">
                  <div className="flex items-center gap-3">
                    <ShieldAlert size={20} className="text-amber" />
                    <h3 className="text-sm font-black uppercase text-amber">Connectivity Protocol</h3>
                  </div>
                  <div className="space-y-4">
                    <div className="flex gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber/20 flex items-center justify-center text-amber text-[10px] font-black shrink-0">1</div>
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium">Generate an API key on your institutional exchange with <strong>Withdrawals Disabled</strong>.</p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber/20 flex items-center justify-center text-amber text-[10px] font-black shrink-0">2</div>
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium">Whitelist the AlphaForge Node IP cluster for ultra-low latency execution.</p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber/20 flex items-center justify-center text-amber text-[10px] font-black shrink-0">3</div>
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium">Confirm the cryptographically signed handshake to initialize signal replication.</p>
                    </div>
                  </div>
                  <Button className="w-full h-12 bg-amber text-amber-foreground font-black uppercase text-[10px] rounded-xl mt-4">
                    Review API Security Guide
                  </Button>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Risk Management Tab */}
        <TabsContent value="risk" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <SpotlightCard className="p-8 max-w-3xl">
            <div className="space-y-8">
              <div className="space-y-2">
                <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                  <Sliders size={16} className="text-primary" /> Global Risk Constraints
                </h3>
                <p className="text-[10px] text-text-muted font-bold uppercase">These limits override all individual strategy parameters</p>
              </div>

              <div className="grid gap-8">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Label className="text-xs font-bold uppercase">Max Portfolio Exposure (%)</Label>
                    <Badge variant="outline" className="text-primary font-mono">25.0%</Badge>
                  </div>
                  <div className="py-4">
                    <Slider defaultValue={[25]} max={100} step={1} />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Label className="text-xs font-bold uppercase">Stop-Loss Override (Global %)</Label>
                    <Badge variant="outline" className="text-red font-mono">15.0%</Badge>
                  </div>
                  <div className="py-4">
                    <Slider defaultValue={[15]} max={50} step={0.5} />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-border-subtle">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                    <div className="space-y-0.5">
                      <Label className="text-[10px] font-black uppercase">Auto-Deleverage</Label>
                      <p className="text-[9px] text-text-muted font-bold uppercase">Reduce risk during high volatility</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                    <div className="space-y-0.5">
                      <Label className="text-[10px] font-black uppercase">Capital Lock</Label>
                      <p className="text-[9px] text-text-muted font-bold uppercase">Disable trades on -10% daily drawdown</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>
              </div>

              <Button className="w-full h-12 bg-primary text-primary-foreground font-black uppercase text-xs rounded-xl">
                Commit Risk Constraints
              </Button>
            </div>
          </SpotlightCard>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="notifications" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <SpotlightCard className="p-8 max-w-3xl">
            <div className="space-y-8">
              <div className="space-y-2">
                <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                  <Bell size={16} className="text-primary" /> Alert Infrastructure
                </h3>
                <p className="text-[10px] text-text-muted font-bold uppercase">Configure real-time signal and system notifications</p>
              </div>

              <div className="space-y-6">
                <div className="space-y-4">
                  <h4 className="text-[10px] font-black uppercase text-primary border-b border-primary/10 pb-2">Trading Alerts</h4>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase">Signal Execution</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase">Position Closure (PnL)</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase">Liquidation Warning</Label>
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="space-y-4 pt-4">
                  <h4 className="text-[10px] font-black uppercase text-primary border-b border-primary/10 pb-2">System Alerts</h4>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase">Node Connectivity Interrupt</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase">API Handshake Expiry</Label>
                    <Switch />
                  </div>
                </div>
              </div>
            </div>
          </SpotlightCard>
        </TabsContent>

        {/* Audit Log Tab */}
        <TabsContent value="audit" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <SpotlightCard className="p-0 overflow-hidden border-border-subtle">
            <div className="p-6 border-b border-border-subtle bg-elevated/20 flex justify-between items-center">
              <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                <FileText size={16} className="text-primary" /> Terminal Audit Trail
              </h3>
              <Button variant="ghost" size="sm" className="text-[9px] font-black uppercase text-text-muted hover:text-text-primary">
                Export ISO-27001 Log
              </Button>
            </div>
            <Table>
              <TableHeader className="bg-elevated/50">
                <TableRow className="border-border-subtle hover:bg-transparent">
                  <TableHead className="text-[10px] font-black uppercase">Timestamp (UTC)</TableHead>
                  <TableHead className="text-[10px] font-black uppercase">Action Node</TableHead>
                  <TableHead className="text-[10px] font-black uppercase">Cluster Entity</TableHead>
                  <TableHead className="text-[10px] font-black uppercase text-right">Verification</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockAuditLogs.map((log) => (
                  <TableRow key={log.id} className="border-border-subtle hover:bg-elevated/20 group">
                    <TableCell className="font-mono text-[10px] text-text-muted">{log.timestamp}</TableCell>
                    <TableCell className="font-bold text-xs uppercase">{log.action}</TableCell>
                    <TableCell className="text-[10px] font-bold text-text-muted uppercase">{log.target}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="text-[9px] font-black uppercase border-green/30 text-green">{log.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </SpotlightCard>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="legal" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <SpotlightCard className="p-8 space-y-6">
              <div className="flex items-center gap-3">
                <Scale size={20} className="text-primary" />
                <h3 className="text-sm font-black uppercase tracking-tight">Institutional Jurisdiction</h3>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase text-text-muted">Operating Region</Label>
                  <Select defaultValue="us-institutional">
                    <SelectTrigger className="bg-elevated/30 border-border-subtle h-12 font-bold uppercase text-[10px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="glass">
                      <SelectItem value="us-institutional">United States (Institutional)</SelectItem>
                      <SelectItem value="eu-professional">European Union (Professional)</SelectItem>
                      <SelectItem value="apac-qualified">Asia Pacific (Qualified)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-2">
                  <div className="flex items-center gap-2 text-primary">
                    <Info size={14} />
                    <span className="text-[10px] font-black uppercase">Regulatory Notice</span>
                  </div>
                  <p className="text-[10px] text-text-secondary leading-relaxed font-medium uppercase">Your node configuration is verified for institutional use under Regulation AF-2024. All trade telemetry is archived for system transparency.</p>
                </div>
              </div>
            </SpotlightCard>

            <SpotlightCard className="p-8 space-y-6">
              <div className="flex items-center gap-3">
                <Database size={20} className="text-primary" />
                <h3 className="text-sm font-black uppercase tracking-tight">Data Integrity & Privacy</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                  <span className="text-[10px] font-black uppercase">GDPR/CCPA Compliance</span>
                  <Badge className="bg-green/20 text-green uppercase text-[9px] font-black">Active</Badge>
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                  <span className="text-[10px] font-black uppercase">Alpha Retention Period</span>
                  <span className="text-[10px] font-bold text-text-muted uppercase">90 Days</span>
                </div>
                <Button variant="ghost" className="w-full h-10 text-[9px] font-black uppercase border border-border-subtle rounded-lg">
                  Request Data Archive Export
                </Button>
                <Button variant="ghost" className="w-full h-10 text-[9px] font-black uppercase text-red hover:bg-red/10 border border-red/10 rounded-lg">
                  Initiate Node Termination & Purge
                </Button>
              </div>
            </SpotlightCard>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
