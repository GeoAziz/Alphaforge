'use client';

import { useState, useEffect } from 'react';
import { useFirestore, useUser, useDoc, useCollection, useMemoFirebase } from '@/firebase';
import { doc, collection, query, orderBy, limit } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { UserProfile, ConnectedExchange, AuditLogEntry, KYCStatus, RiskScore } from '@/lib/types';
import { 
  User, 
  Shield, 
  Key, 
  Globe, 
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
  ShieldCheck,
  ArrowRight,
  Info,
  Smartphone,
  Fingerprint,
  AlertCircle,
  CheckCircle2,
  Globe2,
  RefreshCw,
  Eye,
  Mail,
  MessageSquare
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';

export default function SettingsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [isSaving, setIsSaving] = useState(false);
  const [kyc, setKyc] = useState<KYCStatus | null>(null);
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [is2faEnabled, setIs2faEnabled] = useState(false);

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

  useEffect(() => {
    if (user) {
      api.user.getKYC(user.uid).then(setKyc);
      api.user.getRiskScore(user.uid).then(setRiskScore);
      api.system.getAuditLogs(user.uid).then(setAuditLogs);
    }
  }, [user]);

  function handleUpdateProfile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!profileRef) return;
    setIsSaving(true);
    
    const formData = new FormData(e.currentTarget);
    const updates = {
      name: formData.get('name') as string,
      riskTolerance: formData.get('riskTolerance') as string,
    };

    setDocumentNonBlocking(profileRef, updates, { merge: true });
    setTimeout(() => setIsSaving(false), 800);
  }

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
    <div className="p-8 space-y-8 pb-32 max-w-7xl mx-auto animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Terminal Control Center</h1>
        <p className="text-muted-foreground text-sm font-medium">Configure global risk parameters, security protocols, and institutional API connectivity.</p>
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
              <Sliders size={14} /> Risk Engine
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
            <TabsTrigger value="verification" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Fingerprint size={14} /> Verification
            </TabsTrigger>
            <TabsTrigger value="legal" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all">
              <Scale size={14} /> Compliance
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
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
                      <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center text-primary border border-primary/30 shadow-[0_0_20px_rgba(96,165,250,0.2)]">
                        <Shield size={24} />
                      </div>
                      <div>
                        <div className="text-lg font-black uppercase tracking-tight">Alpha {profile?.plan || 'Free'} Core</div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Institutional grade signals & latency</p>
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
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Connection Status</span>
                    <Badge className="bg-green/20 text-green border-green/30 uppercase text-[9px] font-black">Live & Synced</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Terminal Cluster</span>
                    <span className="text-[10px] font-mono font-black">AF-NODE-US-01</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">API Latency</span>
                    <span className="text-[10px] font-mono font-black text-primary">14.2 ms</span>
                  </div>
                  <div className="pt-4 mt-4 border-t border-border-subtle flex justify-between items-center">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Last Handshake</span>
                    <span className="text-[9px] font-mono font-bold">{new Date().toLocaleTimeString()}</span>
                  </div>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Connectivity Tab */}
        <TabsContent value="exchanges" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
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
                      <Button variant="ghost" className="flex-1 h-9 text-[9px] font-black uppercase text-red hover:bg-red/10 rounded-lg transition-colors">
                        <Trash2 size={12} className="mr-2" /> Terminate Connection
                      </Button>
                    </div>
                  </SpotlightCard>
                ))}

                {(!exchanges || exchanges.length === 0) && (
                  <div className="col-span-full h-60 flex flex-col items-center justify-center border border-dashed border-border-subtle rounded-3xl bg-surface/30 text-center space-y-4 p-8">
                    <div className="w-16 h-16 rounded-full bg-elevated flex items-center justify-center text-text-muted">
                      <Database size={32} />
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm font-black uppercase tracking-tight">No active API handshakes detected</div>
                      <p className="text-[10px] text-text-muted font-bold uppercase">Initialize a connection to enable algorithmic trading nodes.</p>
                    </div>
                    <Button variant="outline" className="border-primary/30 text-primary uppercase text-[10px] font-black h-10 px-8 rounded-xl hover:bg-primary/5">
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
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium uppercase">Generate an API key on your institutional exchange with <strong>Withdrawals Disabled</strong>.</p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber/20 flex items-center justify-center text-amber text-[10px] font-black shrink-0">2</div>
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium uppercase">Whitelist the AlphaForge Node IP cluster for ultra-low latency execution.</p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber/20 flex items-center justify-center text-amber text-[10px] font-black shrink-0">3</div>
                      <p className="text-[11px] text-text-secondary leading-relaxed font-medium uppercase">Confirm the cryptographically signed handshake to initialize signal replication.</p>
                    </div>
                  </div>
                  <Button className="w-full h-12 bg-amber text-amber-foreground font-black uppercase text-[10px] rounded-xl mt-4 hover:opacity-90">
                    Review API Security Guide
                  </Button>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Risk Engine Tab */}
        <TabsContent value="risk" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-7">
              <SpotlightCard className="p-8 space-y-10">
                <div className="space-y-2">
                  <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                    <Sliders size={16} className="text-primary" /> Global Risk Constraints
                  </h3>
                  <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">These limits override all individual strategy parameters</p>
                </div>

                <div className="grid gap-10">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <Label className="text-xs font-bold uppercase tracking-widest">Max Portfolio Exposure (%)</Label>
                      <Badge variant="outline" className="text-primary font-mono font-black h-6 px-3">25.0%</Badge>
                    </div>
                    <div className="py-2">
                      <Slider defaultValue={[25]} max={100} step={1} />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <Label className="text-xs font-bold uppercase tracking-widest">Global Stop-Loss Override (%)</Label>
                      <Badge variant="outline" className="text-red font-mono font-black h-6 px-3">15.0%</Badge>
                    </div>
                    <div className="py-2">
                      <Slider defaultValue={[15]} max={50} step={0.5} />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <Label className="text-xs font-bold uppercase tracking-widest">Max Perpetual Leverage (X)</Label>
                      <Badge variant="outline" className="text-amber font-mono font-black h-6 px-3">10.0X</Badge>
                    </div>
                    <div className="py-2">
                      <Slider defaultValue={[10]} max={50} step={1} />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-border-subtle">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <div className="space-y-0.5">
                        <Label className="text-[10px] font-black uppercase tracking-widest">Auto-Deleverage</Label>
                        <p className="text-[9px] text-text-muted font-bold uppercase">Reduce risk during high volatility</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <div className="space-y-0.5">
                        <Label className="text-[10px] font-black uppercase tracking-widest">Capital Lock</Label>
                        <p className="text-[9px] text-text-muted font-bold uppercase">Disable trades on -10% daily DD</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <Button className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs rounded-2xl shadow-[0_0_20px_rgba(96,165,250,0.3)]">
                  Commit Risk Constraints
                </Button>
              </SpotlightCard>
            </div>

            <div className="col-span-12 lg:col-span-5 space-y-6">
              <SpotlightCard className="p-8 border-primary/10">
                <h3 className="text-sm font-black uppercase text-text-muted mb-8 tracking-widest flex items-center gap-2">
                  <ShieldCheck size={16} className="text-primary" /> Portfolio Risk Score
                </h3>
                
                <div className="flex flex-col items-center text-center space-y-6">
                  <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-full h-full rotate-[-90deg]">
                      <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-border-subtle" />
                      <circle 
                        cx="96" 
                        cy="96" 
                        r="80" 
                        stroke="currentColor" 
                        strokeWidth="12" 
                        fill="transparent" 
                        className={cn(
                          "transition-all duration-1000 ease-out",
                          (riskScore?.score || 0) < 40 ? "text-green" : (riskScore?.score || 0) < 70 ? "text-amber" : "text-red"
                        )} 
                        strokeDasharray="502.6" 
                        strokeDashoffset={502.6 - (502.6 * (riskScore?.score || 0) / 100)} 
                        strokeLinecap="round" 
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-5xl font-black tracking-tighter">{riskScore?.score || '--'}</span>
                      <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">{riskScore?.label || 'Calibrating'}</span>
                    </div>
                  </div>
                  
                  <div className="w-full grid grid-cols-3 gap-2">
                    <div className="p-2 rounded-lg bg-elevated/20 border border-border-subtle">
                      <div className="text-[8px] font-black text-text-muted uppercase mb-1">Vol</div>
                      <div className="text-xs font-bold">{riskScore?.factors.volatility}%</div>
                    </div>
                    <div className="p-2 rounded-lg bg-elevated/20 border border-border-subtle">
                      <div className="text-[8px] font-black text-text-muted uppercase mb-1">Lev</div>
                      <div className="text-xs font-bold">{riskScore?.factors.leverage}%</div>
                    </div>
                    <div className="p-2 rounded-lg bg-elevated/20 border border-border-subtle">
                      <div className="text-[8px] font-black text-text-muted uppercase mb-1">Conc</div>
                      <div className="text-xs font-bold">{riskScore?.factors.concentration}%</div>
                    </div>
                  </div>

                  <p className="text-[10px] text-text-muted font-bold uppercase leading-relaxed max-w-[240px]">
                    Current exposure is optimized for your <span className="text-text-primary">Balanced</span> profile. No immediate action required.
                  </p>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-7 space-y-6">
              <SpotlightCard className="p-8 space-y-8">
                <div className="space-y-2">
                  <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                    <Lock size={16} className="text-primary" /> Institutional Guard
                  </h3>
                  <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Enhanced security protocols for authorized entities</p>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between p-6 rounded-2xl bg-elevated/10 border border-border-subtle hover:bg-elevated/20 transition-all group">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 group-hover:scale-110 transition-transform">
                        <Smartphone size={24} />
                      </div>
                      <div>
                        <div className="text-sm font-black uppercase tracking-tight">Two-Factor Authentication (TOTP)</div>
                        <p className="text-[10px] text-text-muted font-bold uppercase">Required for all institutional withdrawals and API changes</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant="outline" className="text-[9px] font-black uppercase border-red/30 text-red px-3">Disabled</Badge>
                      <Button size="sm" className="bg-primary text-primary-foreground font-black uppercase text-[10px] h-9 px-6 rounded-lg">Setup 2FA</Button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-6 rounded-2xl bg-elevated/10 border border-border-subtle hover:bg-elevated/20 transition-all group">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 group-hover:scale-110 transition-transform">
                        <Key size={24} />
                      </div>
                      <div>
                        <div className="text-sm font-black uppercase tracking-tight">Access Password</div>
                        <p className="text-[10px] text-text-muted font-bold uppercase">Last synchronized: 45 days ago</p>
                      </div>
                    </div>
                    <Button variant="ghost" className="h-9 px-6 text-[10px] font-black uppercase text-primary hover:bg-primary/10 rounded-lg">Update Cluster</Button>
                  </div>
                </div>
              </SpotlightCard>

              <SpotlightCard className="p-8">
                <h3 className="text-xs font-black uppercase text-text-muted mb-6 tracking-widest">Authorized Node Sessions</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border-subtle">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
                      <div>
                        <div className="text-xs font-bold">This Terminal (Chrome / macOS)</div>
                        <div className="text-[9px] text-text-muted font-bold uppercase tracking-tighter">IP: 192.168.1.104 | UTC-05</div>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-[8px] font-black border-green/30 text-green uppercase">Primary</Badge>
                  </div>
                  <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border-subtle opacity-60 grayscale hover:opacity-100 hover:grayscale-0 transition-all cursor-default">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-text-muted" />
                      <div>
                        <div className="text-xs font-bold">Mobile Node (iOS / iPhone 15)</div>
                        <div className="text-[9px] text-text-muted font-bold uppercase tracking-tighter">Last Active: 2h ago</div>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red hover:bg-red/10 rounded-lg"><Trash2 size={14} /></Button>
                  </div>
                </div>
              </SpotlightCard>
            </div>

            <div className="col-span-12 lg:col-span-5">
              <SpotlightCard variant="accent" className="p-8 border-primary/20 bg-primary/5">
                <div className="space-y-6">
                  <div className="flex items-center gap-3">
                    <ShieldCheck size={20} className="text-primary" />
                    <h3 className="text-sm font-black uppercase tracking-tight">Institutional Shield</h3>
                  </div>
                  <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle flex gap-3 items-start">
                      <Info size={14} className="text-primary mt-1 shrink-0" />
                      <p className="text-[10px] text-text-secondary font-bold uppercase leading-relaxed">
                        AlphaForge nodes use <span className="text-primary">SHA-256</span> encryption for all API keys at rest. Your credentials never touch the public internet unencrypted.
                      </p>
                    </div>
                    <div className="p-4 rounded-xl bg-surface/50 border border-border-subtle flex gap-3 items-start">
                      <ShieldAlert size={14} className="text-amber mt-1 shrink-0" />
                      <p className="text-[10px] text-text-secondary font-bold uppercase leading-relaxed">
                        Session termination is immediate. If you suspect an unauthorized handshake, click the <span className="text-red">Panic Node</span> button to kill all active API bridges.
                      </p>
                    </div>
                  </div>
                  <Button variant="destructive" className="w-full h-12 font-black uppercase text-[10px] rounded-xl gap-2 shadow-lg">
                    <ShieldAlert size={14} /> Immediate Panic Node Termination
                  </Button>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="notifications" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <SpotlightCard className="p-8 space-y-8">
              <div className="space-y-2">
                <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                  <Bell size={16} className="text-primary" /> Alert Infrastructure
                </h3>
                <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Configure real-time signal and system notifications</p>
              </div>

              <div className="space-y-6">
                <div className="space-y-4">
                  <h4 className="text-[9px] font-black uppercase text-primary border-b border-primary/10 pb-2 tracking-widest">Trading Alpha Nodes</h4>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase tracking-widest">High-Confidence Signals</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase tracking-widest">Position Closure (PnL)</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase tracking-widest">Liquidation Warning</Label>
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="space-y-4 pt-4">
                  <h4 className="text-[9px] font-black uppercase text-primary border-b border-primary/10 pb-2 tracking-widest">System Health Nodes</h4>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase tracking-widest">Node Connectivity Sync</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-bold uppercase tracking-widest">API Handshake Expiry</Label>
                    <Switch />
                  </div>
                </div>
              </div>
            </SpotlightCard>

            <SpotlightCard className="p-8 space-y-8">
              <h3 className="text-sm font-black uppercase text-text-muted tracking-widest">Channel Integration</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/10 border border-border-subtle group hover:border-primary/30 transition-all">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-text-muted group-hover:text-primary transition-colors">
                      <Mail size={20} />
                    </div>
                    <div>
                      <div className="text-xs font-black uppercase">Email Node</div>
                      <div className="text-[9px] text-text-muted font-bold">trader@alphaforge.ai</div>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-[8px] font-black border-green/30 text-green uppercase px-3">Active</Badge>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/10 border border-border-subtle group hover:border-primary/30 transition-all">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-text-muted group-hover:text-primary transition-colors">
                      <MessageSquare size={20} />
                    </div>
                    <div>
                      <div className="text-xs font-black uppercase">Telegram Cluster</div>
                      <div className="text-[9px] text-text-muted font-bold">@AlphaNode_Secure</div>
                    </div>
                  </div>
                  <Button size="sm" variant="ghost" className="h-8 text-[9px] font-black uppercase text-primary hover:bg-primary/10 rounded-lg px-4">Connect</Button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/10 border border-border-subtle group hover:border-primary/30 transition-all opacity-50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-text-muted">
                      <Globe2 size={20} />
                    </div>
                    <div>
                      <div className="text-xs font-black uppercase">Webhook Web-bridge</div>
                      <div className="text-[9px] text-text-muted font-bold uppercase tracking-widest italic">Institutional Tier 2+ Required</div>
                    </div>
                  </div>
                  <Lock size={14} className="text-text-muted mr-4" />
                </div>
              </div>
            </SpotlightCard>
          </div>
        </TabsContent>

        {/* Audit Log Tab */}
        <TabsContent value="audit" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <SpotlightCard className="p-0 overflow-hidden border-border-subtle bg-surface/30 backdrop-blur-md">
            <div className="p-6 border-b border-border-subtle bg-elevated/20 flex justify-between items-center">
              <div className="space-y-1">
                <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
                  <FileText size={16} className="text-primary" /> Terminal Audit Trail
                </h3>
                <p className="text-[10px] text-text-muted font-bold uppercase">Immutable action log for node compliance</p>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" className="h-9 px-4 border-border-subtle text-[9px] font-black uppercase gap-2 hover:bg-elevated rounded-xl">
                  <RefreshCw size={12} /> Sync Feed
                </Button>
                <Button variant="ghost" size="sm" className="h-9 px-4 text-[9px] font-black uppercase text-primary hover:bg-primary/10 rounded-xl gap-2">
                  <Database size={12} /> Export ISO-27001 Log
                </Button>
              </div>
            </div>
            <Table>
              <TableHeader className="bg-elevated/50">
                <TableRow className="border-border-subtle hover:bg-transparent">
                  <TableHead className="text-[10px] font-black uppercase tracking-widest">Timestamp (UTC)</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest">Action Node</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest">Cluster Entity</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest text-right">Verification</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditLogs.map((log) => (
                  <TableRow key={log.id} className="border-border-subtle hover:bg-elevated/20 group transition-all">
                    <TableCell className="font-mono text-[10px] text-text-muted">{new Date(log.timestamp).toLocaleString()}</TableCell>
                    <TableCell className="font-black text-xs uppercase tracking-tighter">{log.action}</TableCell>
                    <TableCell className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{log.target}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className={cn(
                        "text-[9px] font-black uppercase border-green/30 text-green",
                        log.status === 'Warning' && "border-amber/30 text-amber",
                        log.status === 'Failure' && "border-red/30 text-red"
                      )}>{log.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="p-4 border-t border-border-subtle bg-elevated/10 flex justify-between items-center">
              <span className="text-[9px] font-black uppercase text-text-muted tracking-widest">Total Resolved Actions: {auditLogs.length}</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="h-8 w-8 p-0 border-border-subtle rounded-lg" disabled><ArrowRight size={14} className="rotate-180" /></Button>
                <Button variant="outline" size="sm" className="h-8 w-8 p-0 border-border-subtle rounded-lg" disabled><ArrowRight size={14} /></Button>
              </div>
            </div>
          </SpotlightCard>
        </TabsContent>

        {/* Verification Tab */}
        <TabsContent value="verification" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-8 space-y-6">
              <SpotlightCard className="p-8 space-y-10">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2">
                      <Fingerprint size={16} className="text-primary" /> Identity Verification
                    </h3>
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Mandatory KYC/AML audit for institutional node access</p>
                  </div>
                  <Badge className="bg-green/20 text-green border-green/30 uppercase text-[10px] font-black h-8 px-4">Level {kyc?.level} Verified</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-6 rounded-2xl bg-elevated/10 border border-border-subtle space-y-4">
                    <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-primary">
                      <CheckCircle2 size={20} />
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-black uppercase tracking-tight">Identity Audit</div>
                      <div className="text-[10px] text-green font-bold uppercase">Handshake Passed</div>
                    </div>
                  </div>
                  <div className="p-6 rounded-2xl bg-elevated/10 border border-border-subtle space-y-4">
                    <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-primary">
                      <CheckCircle2 size={20} />
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-black uppercase tracking-tight">Address Node</div>
                      <div className="text-[10px] text-green font-bold uppercase">Residency Synced</div>
                    </div>
                  </div>
                  <div className="p-6 rounded-2xl bg-elevated/10 border border-border-subtle space-y-4 relative overflow-hidden group">
                    <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-text-muted">
                      <AlertCircle size={20} />
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-black uppercase tracking-tight text-text-muted">Wealth Proof</div>
                      <div className="text-[10px] text-text-muted font-bold uppercase">Institutional Tier 3 Req.</div>
                    </div>
                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
                      <Button size="sm" className="h-8 bg-primary text-primary-foreground font-black text-[9px] uppercase px-4 rounded-lg">Upgrade Tier</Button>
                    </div>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-primary/5 border border-primary/10 flex flex-col md:flex-row justify-between items-center gap-6">
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary mt-1 shrink-0"><Shield size={20} /></div>
                    <div>
                      <div className="text-sm font-black uppercase tracking-tight">Institutional Tier 2+ Benefits</div>
                      <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest leading-relaxed">
                        Unlimited algorithmic clusters, sub-10ms priority execution, and dedicated node support.
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="border-primary/50 text-primary uppercase text-[10px] font-black h-10 px-8 rounded-xl shrink-0">Review Tier Roadmap</Button>
                </div>
              </SpotlightCard>
            </div>

            <div className="col-span-12 lg:col-span-4">
              <SpotlightCard className="p-8 space-y-6 h-full">
                <h3 className="text-xs font-black uppercase text-text-muted tracking-widest">KYC Intelligence</h3>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <div className="text-[9px] font-black uppercase text-text-muted tracking-widest">Verified At</div>
                    <div className="text-sm font-mono font-bold">{kyc?.verifiedAt ? new Date(kyc.verifiedAt).toLocaleDateString() : 'N/A'}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-[9px] font-black uppercase text-text-muted tracking-widest">Residency Node</div>
                    <div className="text-sm font-bold uppercase tracking-tight">USA (Institutional)</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-[9px] font-black uppercase text-text-muted tracking-widest">AML Risk Cluster</div>
                    <Badge variant="outline" className="border-green/30 text-green uppercase text-[9px] font-black">Minimal Alpha-Risk</Badge>
                  </div>
                </div>
                <div className="pt-6 mt-6 border-t border-border-subtle">
                  <Button variant="ghost" className="w-full text-red hover:bg-red/10 h-10 text-[9px] font-black uppercase rounded-lg gap-2">
                    <ShieldAlert size={14} /> Appeal Verification Status
                  </Button>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="legal" className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <SpotlightCard className="p-8 space-y-6">
              <div className="flex items-center gap-3">
                <Scale size={20} className="text-primary" />
                <h3 className="text-sm font-black uppercase tracking-tight">Institutional Jurisdiction</h3>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase text-text-muted tracking-widest">Operating Region</Label>
                  <Select defaultValue="us-institutional">
                    <SelectTrigger className="bg-elevated/30 border-border-subtle h-12 font-bold uppercase text-[10px] tracking-widest">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="glass border-border-subtle">
                      <SelectItem value="us-institutional">United States (Institutional)</SelectItem>
                      <SelectItem value="eu-professional">European Union (Professional)</SelectItem>
                      <SelectItem value="apac-qualified">Asia Pacific (Qualified)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-2">
                  <div className="flex items-center gap-2 text-primary">
                    <Info size={14} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Regulatory Notice</span>
                  </div>
                  <p className="text-[10px] text-text-secondary leading-relaxed font-medium uppercase tracking-widest">Your node configuration is verified for institutional use under Regulation AF-2024. All trade telemetry is archived for system transparency.</p>
                </div>
              </div>
            </SpotlightCard>

            <SpotlightCard className="p-8 space-y-6">
              <div className="flex items-center gap-3">
                <Database size={20} className="text-primary" />
                <h3 className="text-sm font-black uppercase tracking-tight">Data Integrity & Sovereignty</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                  <span className="text-[10px] font-black uppercase tracking-widest">GDPR/CCPA Compliance</span>
                  <Badge className="bg-green/20 text-green border-green/30 uppercase text-[9px] font-black px-3">Active</Badge>
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                  <span className="text-[10px] font-black uppercase tracking-widest">Alpha Retention Period</span>
                  <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">90 Days</span>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <Button variant="outline" className="h-10 text-[9px] font-black uppercase border-border-subtle rounded-xl hover:bg-elevated transition-colors">
                    Request Archive Export
                  </Button>
                  <Button variant="ghost" className="h-10 text-[9px] font-black uppercase text-red hover:bg-red/10 border border-red/10 rounded-xl transition-colors">
                    Initiate Node Purge
                  </Button>
                </div>
              </div>
            </SpotlightCard>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
