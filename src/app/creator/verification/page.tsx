'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useUser } from '@/firebase';
import { CreatorVerificationStatus } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ShieldCheck, Activity, Award, CheckCircle2, Clock, AlertCircle, ChevronDown, ChevronUp, FileText, BarChart3, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CreatorVerificationPage() {
  const { user } = useUser();
  const [pipeline, setPipeline] = useState<CreatorVerificationStatus[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      api.creator.getVerificationPipeline(user.uid).then(data => {
        setPipeline(data);
        setIsLoading(false);
      });
    }
  }, [user]);

  if (!user) return <div className="p-8 text-center uppercase font-black">Authorized Creator Access Required.</div>;

  return (
    <div className="p-8 space-y-8 pb-32 max-w-6xl mx-auto animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Creator Dashboard</h1>
        <p className="text-muted-foreground text-sm font-medium">Manage your alpha clusters and track strategy verification pipeline status.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SpotlightCard className="p-6 border-primary/10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20"><Award size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Creator Level</div>
              <div className="text-xl font-black uppercase">Tier 1 Institutional</div>
            </div>
          </div>
          <div className="text-[10px] text-primary font-bold uppercase flex items-center gap-1"><CheckCircle2 size={10} /> Verified Strategy Provider</div>
        </SpotlightCard>
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent border border-accent/20"><Activity size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Active Clusters</div>
              <div className="text-xl font-black">4 Nodes Live</div>
            </div>
          </div>
          <div className="text-[10px] text-accent font-bold uppercase flex items-center gap-1"><Clock size={10} /> 99.9% Uptime</div>
        </SpotlightCard>
        <SpotlightCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-green/10 flex items-center justify-center text-green border border-green/20"><BarChart3 size={20} /></div>
            <div>
              <div className="text-[10px] font-black uppercase text-text-muted">Total Managed</div>
              <div className="text-xl font-black text-green">$42.5M AUM</div>
            </div>
          </div>
          <div className="text-[10px] text-green font-bold uppercase flex items-center gap-1"><TrendingUp size={10} /> +124% ROI Trailing 12M</div>
        </SpotlightCard>
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-sm font-black uppercase tracking-widest text-text-muted flex items-center gap-2">
            <ShieldCheck size={16} className="text-primary" /> Verification Pipeline
          </h2>
          <Button size="sm" className="bg-primary text-primary-foreground font-black uppercase text-[10px] h-9 px-6 rounded-lg">Submit New Alpha Cluster</Button>
        </div>

        <div className="space-y-4">
          {isLoading ? (
            Array(2).fill(0).map((_, i) => <div key={i} className="h-24 rounded-2xl bg-elevated/20 animate-pulse border border-border-subtle" />)
          ) : pipeline.map((item) => (
            <SpotlightCard key={item.strategyId} className="overflow-hidden border-border-subtle transition-all">
              <div className="p-6 flex items-center justify-between cursor-pointer group" onClick={() => setExpandedId(expandedId === item.strategyId ? null : item.strategyId)}>
                <div className="flex items-center gap-6">
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl border",
                    item.overallStatus === 'Active' ? "bg-green/10 text-green border-green/20" : "bg-amber/10 text-amber border-amber/20"
                  )}>
                    {item.strategyName[0]}
                  </div>
                  <div>
                    <h3 className="text-xl font-black tracking-tighter uppercase">{item.strategyName}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex items-center gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <div key={i} className={cn("w-3 h-1 rounded-full", i < item.currentStage ? (item.overallStatus === 'Active' ? "bg-green" : "bg-amber") : "bg-elevated")} />
                        ))}
                      </div>
                      <span className="text-[9px] font-black text-text-muted uppercase">Stage {item.currentStage}/5 Verified</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <Badge className={cn(
                    "uppercase font-black text-[10px] h-7 px-4",
                    item.overallStatus === 'Active' ? "bg-green/20 text-green" : "bg-amber/20 text-amber"
                  )}>{item.overallStatus}</Badge>
                  {expandedId === item.strategyId ? <ChevronUp size={20} className="text-text-muted" /> : <ChevronDown size={20} className="text-text-muted group-hover:text-text-primary transition-colors" />}
                </div>
              </div>

              {expandedId === item.strategyId && (
                <div className="p-8 border-t border-border-subtle bg-elevated/10 space-y-8 animate-in slide-in-from-top-4 duration-300">
                  <div className="relative pl-8 space-y-10">
                    <div className="absolute left-3.5 top-2 bottom-2 w-px bg-border-subtle" />
                    {item.steps.map((step, index) => (
                      <div key={step.id} className="relative">
                        <div className={cn(
                          "absolute -left-[25px] top-1 w-4 h-4 rounded-full border-4 border-surface",
                          step.status === 'Completed' ? "bg-green" : step.status === 'In Progress' ? "bg-amber animate-pulse" : "bg-elevated"
                        )} />
                        <div className="space-y-1">
                          <div className="flex items-center gap-3">
                            <h4 className={cn(
                              "text-sm font-black uppercase tracking-tight",
                              step.status === 'Pending' && "text-text-muted"
                            )}>{step.name}</h4>
                            <Badge variant="outline" className={cn(
                              "text-[8px] font-black uppercase h-4 px-1.5",
                              step.status === 'Completed' ? "text-green border-green/20" : step.status === 'In Progress' ? "text-amber border-amber/20" : "text-text-muted border-border-subtle"
                            )}>{step.status}</Badge>
                          </div>
                          <p className="text-[11px] text-text-muted font-medium uppercase leading-relaxed max-w-md">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-8 border-t border-border-subtle flex flex-col md:flex-row gap-4 items-center justify-between">
                    <div className="flex gap-2">
                      <Button variant="outline" className="border-border-subtle text-[10px] font-black uppercase h-10 px-6 gap-2 rounded-lg hover:bg-elevated">
                        <FileText size={14} /> Technical Whitepaper
                      </Button>
                      <Button variant="outline" className="border-border-subtle text-[10px] font-black uppercase h-10 px-6 gap-2 rounded-lg hover:bg-elevated">
                        <BarChart3 size={14} /> Audit Trail Export
                      </Button>
                    </div>
                    {item.overallStatus === 'Denied' && (
                      <Button variant="destructive" className="h-10 text-[10px] font-black uppercase px-8 rounded-lg gap-2">
                        <AlertCircle size={14} /> Appeal Verification Node
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </SpotlightCard>
          ))}
        </div>
      </div>
    </div>
  );
}
