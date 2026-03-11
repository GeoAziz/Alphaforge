
'use client';

import { useState } from 'react';
import { useFirestore, useUser, useDoc, useCollection, useMemoFirebase } from '@/firebase';
import { doc, collection } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { UserProfile, ConnectedExchange } from '@/lib/types';
import { 
  User, 
  Shield, 
  Key, 
  Bell, 
  Globe, 
  CreditCard, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';

export default function SettingsPage() {
  const { user } = useUser();
  const db = useFirestore();
  const { toast } = useToast();
  const [isSaving, setIsSaving] = useState(false);

  const profileRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid);
  }, [user, db]);

  const exchangesQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return collection(db, 'users', user.uid, 'connected_exchanges');
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

    // Pattern 1: Non-blocking mutation with merge
    setDocumentNonBlocking(profileRef, updates, { merge: true });
    
    // Optimistically update state
    setTimeout(() => setIsSaving(false), 500);
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Shield size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase">Terminal Access Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to manage institutional terminal configurations and exchange connectivity.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20 max-w-6xl mx-auto">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Terminal Settings</h1>
        <p className="text-muted-foreground text-sm">Configure global risk parameters and algorithmic API connectivity.</p>
      </header>

      <Tabs defaultValue="profile" className="space-y-8">
        <TabsList className="bg-elevated/50 p-1 rounded-xl border border-border-subtle h-12">
          <TabsTrigger value="profile" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg">
            <User size={14} /> Profile
          </TabsTrigger>
          <TabsTrigger value="exchanges" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg">
            <Globe size={14} /> Connectivity
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg">
            <Key size={14} /> Security
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2 px-6 font-bold uppercase text-[10px] data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg">
            <CreditCard size={14} /> Billing
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="grid grid-cols-12 gap-8">
            <SpotlightCard className="col-span-12 lg:col-span-7 p-8">
              <form onSubmit={handleUpdateProfile} className="space-y-6">
                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase text-text-muted mb-4">Account Information</h3>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-text-muted">Display Name</label>
                    <Input name="name" defaultValue={profile?.name || ''} className="bg-elevated/30 border-border-subtle h-12" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-text-muted">Node Identifier</label>
                    <Input disabled value={user.email || 'Anonymous Guest Session'} className="bg-elevated/10 border-border-subtle h-12 opacity-50" />
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-border-subtle">
                  <h3 className="text-sm font-bold uppercase text-text-muted mb-4">Risk Preferences</h3>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-text-muted">Global Risk Tolerance</label>
                    <select 
                      name="riskTolerance" 
                      defaultValue={profile?.riskTolerance || 'balanced'}
                      className="w-full h-12 rounded-md border border-border-subtle bg-elevated/30 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="conservative">Conservative</option>
                      <option value="balanced">Balanced</option>
                      <option value="aggressive">Aggressive</option>
                    </select>
                  </div>
                </div>

                <Button type="submit" disabled={isSaving} className="w-full h-12 bg-primary text-primary-foreground font-black uppercase text-xs gap-2">
                  {isSaving && <Loader2 className="animate-spin" size={16} />}
                  Save Configuration
                </Button>
              </form>
            </SpotlightCard>

            <div className="col-span-12 lg:col-span-5 space-y-6">
              <SpotlightCard variant="accent" className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                    <Shield size={20} />
                  </div>
                  <div>
                    <div className="text-xs font-black uppercase">Intelligence Tier</div>
                    <Badge className="bg-primary/20 text-primary border-primary/30 uppercase text-[10px] font-black">{profile?.plan || 'Free'} Core</Badge>
                  </div>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed mb-6">
                  Your node is operating on the {profile?.plan || 'Free'} tier. Upgrade for ultra-low latency signals and institutional marketplace access.
                </p>
                <Button variant="outline" className="w-full border-primary/50 text-primary hover:bg-primary/5 font-black uppercase text-[10px]">
                  Upgrade Intelligence Node
                </Button>
              </SpotlightCard>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="exchanges" className="animate-in fade-in slide-in-from-left-4 duration-300">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase text-text-muted">Institutional Connectivity</h3>
              <Button size="sm" className="bg-primary h-8 text-[10px] font-black uppercase gap-2">
                <Plus size={14} /> Connect API
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {exchanges?.map(ex => (
                <SpotlightCard key={ex.id} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center font-black text-lg">
                        {ex.exchange[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="font-bold capitalize">{ex.exchange}</div>
                        <div className="text-[10px] text-text-muted font-bold uppercase font-mono">Synced: {new Date(ex.connectedAt).toLocaleDateString()}</div>
                      </div>
                    </div>
                    <Badge className="bg-green/10 text-green border-green/20 uppercase text-[9px] font-black">Online</Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" className="h-8 px-2 text-[9px] font-black uppercase text-red hover:bg-red/10">
                      <Trash2 size={12} className="mr-1" /> Terminate Connection
                    </Button>
                  </div>
                </SpotlightCard>
              ))}

              {(!exchanges || exchanges.length === 0) && (
                <div className="col-span-2 h-40 flex flex-col items-center justify-center border border-dashed border-border-subtle rounded-2xl bg-surface/30 text-center">
                  <Globe className="text-text-muted mb-2" size={24} />
                  <div className="text-xs font-bold text-text-muted uppercase">Scanning for active API handshakes...</div>
                </div>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
