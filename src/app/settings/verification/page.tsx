'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { KYCStatus, CreatorVerificationStatus } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  FileText,
  Camera,
  Upload,
  UserCheck,
  Award,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

export default function VerificationHubPage() {
  const { user } = useUser();
  const [kyc, setKyc] = useState<KYCStatus | null>(null);
  const [creatorPipeline, setCreatorPipeline] = useState<CreatorVerificationStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      Promise.all([
        api.user.getKYC(user.uid),
        api.creator.getVerificationPipeline(user.uid)
      ]).then(([k, p]) => {
        setKyc(k);
        setCreatorPipeline(p);
        setIsLoading(false);
      });
    }
  }, [user]);

  if (!user) return null;

  return (
    <div className="p-8 space-y-10 max-w-5xl mx-auto animate-page pb-32">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none text-text-primary">Verification Handshake</h1>
        <p className="text-text-muted text-sm font-bold uppercase tracking-widest">Institutional Identity & Creator Audit Status</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* KYC Node */}
        <div className="lg:col-span-7 space-y-8">
          <SpotlightCard className="p-8 space-y-8 border-primary/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center border",
                  kyc?.status === 'Verified' ? "bg-green/10 text-green border-green/20" : "bg-amber/10 text-amber border-amber/20"
                )}>
                  <UserCheck size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-black uppercase tracking-tight">Identity Node</h3>
                  <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Status: {kyc?.status}</p>
                </div>
              </div>
              {kyc?.status === 'Verified' && <Badge className="bg-green/20 text-green border-green/30 uppercase font-black text-[9px] h-6 px-3">Verified Level {kyc.level}</Badge>}
            </div>

            {kyc?.status === 'Rejected' && (
              <div className="p-6 rounded-2xl bg-red/5 border border-red/20 space-y-4 animate-in slide-in-from-top-4">
                <div className="flex items-center gap-2 text-red">
                  <ShieldAlert size={18} />
                  <h4 className="text-xs font-black uppercase">Handshake Verification Declined</h4>
                </div>
                <p className="text-[10px] text-text-secondary leading-relaxed font-medium uppercase">
                  Reason: Document unreadable or restricted jurisdiction. Please resubmit high-fidelity scans of your institutional ID.
                </p>
                <div className="flex gap-2">
                  <Button className="h-9 bg-red text-white font-black uppercase text-[9px] px-6 rounded-lg">Resubmit Node Data</Button>
                  <Button variant="ghost" className="h-9 text-text-muted font-black uppercase text-[9px] hover:text-text-primary">Appeal Decision</Button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 rounded-2xl bg-elevated/20 border border-border-subtle flex items-center justify-between group cursor-help">
                <div className="flex items-center gap-3">
                  <Camera size={18} className="text-text-muted group-hover:text-primary transition-colors" />
                  <span className="text-[10px] font-black uppercase tracking-widest">Government ID</span>
                </div>
                {kyc?.status === 'Verified' ? <CheckCircle2 size={16} className="text-green" /> : <Clock size={16} className="text-amber" />}
              </div>
              <div className="p-5 rounded-2xl bg-elevated/20 border border-border-subtle flex items-center justify-between group cursor-help">
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-text-muted group-hover:text-primary transition-colors" />
                  <span className="text-[10px] font-black uppercase tracking-widest">Proof of Address</span>
                </div>
                {kyc?.status === 'Verified' ? <CheckCircle2 size={16} className="text-green" /> : <Clock size={16} className="text-amber" />}
              </div>
            </div>

            <Separator className="bg-border-subtle" />

            <div className="p-6 rounded-2xl bg-primary/5 border border-dashed border-primary/20 space-y-4">
              <h4 className="text-xs font-black uppercase flex items-center gap-2 text-primary">
                <ShieldCheck size={16} /> Data Sovereignty
              </h4>
              <p className="text-[10px] text-text-muted font-bold uppercase leading-relaxed">
                All identity metadata is encrypted via AES-256 and stored in an air-gapped institutional vault. AlphaForge compliance nodes do not have plain-text access to your documents.
              </p>
            </div>
          </SpotlightCard>
        </div>

        {/* Creator Pipeline */}
        <div className="lg:col-span-5 space-y-8">
          <SpotlightCard className="p-8 space-y-8">
            <h3 className="text-sm font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
              <Award size={18} className="text-accent" />
              Creator Audit Pipeline
            </h3>

            <div className="space-y-6">
              {creatorPipeline.length === 0 ? (
                <div className="py-12 text-center space-y-4 opacity-40">
                  <AlertCircle size={32} className="mx-auto text-text-muted" />
                  <p className="text-[10px] font-black uppercase text-text-muted">No active strategy submissions.</p>
                  <Button className="h-10 bg-elevated border-border-subtle text-[9px] font-black uppercase px-6">Apply as Provider</Button>
                </div>
              ) : creatorPipeline.map((strat) => (
                <div key={strat.strategyId} className="space-y-4 p-5 rounded-2xl bg-elevated/10 border border-border-subtle hover:border-accent/30 transition-all group">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="text-sm font-black uppercase tracking-tight text-text-primary group-hover:text-accent transition-colors">{strat.strategyName}</div>
                      <div className="text-[8px] font-black text-text-muted uppercase tracking-widest">Pipeline Cluster ID: {strat.strategyId}</div>
                    </div>
                    <Badge className={cn(
                      "text-[8px] font-black uppercase h-5 px-2",
                      strat.overallStatus === 'Active' ? "bg-green/20 text-green" : "bg-amber/20 text-amber"
                    )}>{strat.overallStatus}</Badge>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-[8px] font-black uppercase text-text-muted">
                      <span>Audit Completion</span>
                      <span>{Math.round((strat.currentStage / 5) * 100)}%</span>
                    </div>
                    <Progress value={(strat.currentStage / 5) * 100} className="h-1 bg-border-subtle" />
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <div className="flex gap-1">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className={cn(
                          "w-2 h-2 rounded-full",
                          i < strat.currentStage ? "bg-accent" : "bg-border-subtle"
                        )} />
                      ))}
                    </div>
                    <Button variant="ghost" className="h-6 text-[8px] font-black uppercase text-accent hover:text-accent/80 p-0 flex items-center gap-1">
                      Examine Node Details <ChevronRight size={10} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-6 bg-accent/5 border-accent/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                <AlertCircle size={16} />
              </div>
              <div className="space-y-0.5">
                <div className="text-[9px] font-black uppercase text-accent">Node Requirements</div>
                <p className="text-[8px] font-bold text-text-muted uppercase leading-relaxed">
                  Alpha providers must maintain a live Sharpe &gt; 1.0 for 28 consecutive days to finalize verification.
                </p>
              </div>
            </div>
          </SpotlightCard>
        </div>
      </div>
    </div>
  );
}
