'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, useFirestore, useDoc, useMemoFirebase } from '@/firebase';
import { doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { 
  Loader2, 
  ArrowRight, 
  ShieldCheck, 
  Zap, 
  TrendingUp, 
  Globe, 
  Bell, 
  Eye, 
  Scale, 
  Database,
  ArrowLeft,
  ShieldAlert,
  Info
} from 'lucide-react';
import { cn } from '@/lib/utils';

const RISK_LEVELS = [
  { id: 'conservative', label: 'Conservative', description: 'Priority on capital preservation and low volatility.', icon: ShieldCheck },
  { id: 'balanced', label: 'Balanced', description: 'Moderate growth with controlled risk exposure.', icon: Zap },
  { id: 'aggressive', label: 'Aggressive', description: 'High-frequency pursuit of alpha with significant exposure.', icon: TrendingUp },
];

export default function OnboardingPage() {
  const { user, isUserLoading } = useUser();
  const db = useFirestore();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState<'next' | 'back'>('next');
  const [name, setName] = useState('');
  const [risk, setRisk] = useState('balanced');
  const [gdpr, setGdpr] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const profileRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid);
  }, [user, db]);

  const { data: profile } = useDoc(profileRef);

  useEffect(() => {
    if (profile?.onboardingComplete) {
      router.push('/');
    }
  }, [profile, router]);

  function handleNext() {
    setDirection('next');
    setStep(s => s + 1);
  }

  function handleBack() {
    setDirection('back');
    setStep(s => s - 1);
  }

  function handleCompleteOnboarding() {
    if (!profileRef || !user) return;
    setIsSubmitting(true);

    const onboardingData = {
      id: user.uid,
      name: name || 'Institutional User',
      email: user.email || '',
      plan: 'free',
      riskTolerance: risk,
      onboardingComplete: true,
      createdAt: new Date().toISOString(),
    };

    setDocumentNonBlocking(profileRef, onboardingData, { merge: true });
    router.push('/');
  }

  if (isUserLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex items-center justify-center bg-background p-6 overflow-hidden">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary mb-4 font-black text-primary-foreground shadow-[0_0_20px_rgba(96,165,250,0.4)]">
            AF
          </div>
          <h1 className="text-4xl font-black uppercase tracking-tighter">Terminal Initialization</h1>
          
          {/* Progress Stepper */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div 
                key={i} 
                className={cn(
                  "h-1 rounded-full transition-all duration-500",
                  step === i + 1 ? "w-8 bg-primary" : i + 1 < step ? "w-4 bg-primary/40" : "w-4 bg-elevated"
                )}
              />
            ))}
          </div>
        </div>

        <div className={cn(
          "transition-all duration-500",
          direction === 'next' ? "animate-step-in" : "animate-step-in"
        )} key={step}>
          <SpotlightCard className="p-10 shadow-2xl border-primary/10 bg-surface/50 backdrop-blur-xl">
            {step === 1 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <h2 className="text-xl font-black uppercase tracking-tight">Identity Handshake</h2>
                  <p className="text-sm text-text-muted leading-relaxed uppercase font-bold text-[10px]">
                    Step 1: AlphaForge requires a node identifier for session persistence and institutional reporting.
                  </p>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-black uppercase text-text-muted">Display Name</Label>
                    <Input 
                      value={name} 
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter your node identifier..."
                      className="h-14 bg-elevated/50 border-border-subtle focus:ring-primary/20 font-bold"
                    />
                  </div>
                </div>
                <Button 
                  onClick={handleNext}
                  disabled={!name}
                  className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 group"
                >
                  Synchronize Connectivity <ArrowRight size={16} />
                </Button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4">
                    <Globe size={24} />
                  </div>
                  <h2 className="text-xl font-black uppercase tracking-tight">Exchange Connectivity</h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    Establish an institutional bridge to your trading platform. AlphaForge uses <span className="text-primary font-bold">idempotent handshake protocols</span> to ensure connection stability.
                  </p>
                  <div className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex gap-3 items-start">
                    <Info size={14} className="text-primary mt-1 shrink-0" />
                    <p className="text-[10px] font-bold text-text-muted uppercase leading-snug">You can skip this step and use the simulated data stream for now.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">Back</Button>
                  <Button onClick={handleNext} className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs">Initialize Sync</Button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <h2 className="text-xl font-black uppercase tracking-tight">Regime Sensitivity</h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    Select your institutional risk tolerance. This calibrates signal filtering and margin exposure alerts.
                  </p>
                  <RadioGroup value={risk} onValueChange={setRisk} className="grid grid-cols-1 gap-4">
                    {RISK_LEVELS.map((level) => (
                      <div key={level.id}>
                        <RadioGroupItem value={level.id} id={level.id} className="peer sr-only" />
                        <Label
                          htmlFor={level.id}
                          className={cn(
                            "flex items-start gap-4 p-4 rounded-xl border border-border-subtle bg-elevated/20 cursor-pointer transition-all hover:bg-elevated/40 peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5",
                            risk === level.id && "border-primary bg-primary/5"
                          )}
                        >
                          <div className={cn(
                            "mt-1 w-8 h-8 rounded-lg flex items-center justify-center",
                            risk === level.id ? "bg-primary text-primary-foreground" : "bg-elevated text-text-muted"
                          )}>
                            <level.icon size={18} />
                          </div>
                          <div className="space-y-1">
                            <div className="font-black text-sm uppercase">{level.label}</div>
                            <div className="text-[11px] text-text-muted leading-snug font-medium">{level.description}</div>
                          </div>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                  <div className="p-4 rounded-xl bg-red/5 border border-red/10 space-y-2">
                    <div className="flex items-center gap-2 text-red">
                      <ShieldAlert size={14} />
                      <span className="text-[10px] font-black uppercase">Regulatory Disclosure</span>
                    </div>
                    <p className="text-[9px] text-text-muted font-bold uppercase leading-tight">Past performance is not indicative of future alpha. Trading derivatives involves significant risk.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">Back</Button>
                  <Button onClick={handleNext} className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs">Commit Risk</Button>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4">
                    <Bell size={24} />
                  </div>
                  <h2 className="text-xl font-black uppercase tracking-tight">Notification Nodes</h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    Enable real-time telemetry for signal execution and risk alerts. AlphaForge nodes synchronize globally for <span className="text-primary font-bold">sub-10ms delivery</span>.
                  </p>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <div className="space-y-0.5">
                        <Label className="text-[10px] font-black uppercase">Alpha Signals</Label>
                        <p className="text-[9px] text-text-muted font-bold uppercase">Real-time trading opportunities</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <div className="space-y-0.5">
                        <Label className="text-[10px] font-black uppercase">Risk Alerts</Label>
                        <p className="text-[9px] text-text-muted font-bold uppercase">Margin and drawdown triggers</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">Back</Button>
                  <Button onClick={handleNext} className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs">Sync Nodes</Button>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4">
                    <Eye size={24} />
                  </div>
                  <h2 className="text-xl font-black uppercase tracking-tight">Terminal Walkthrough</h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    Your institutional workspace is divided into <span className="text-primary font-bold">Intelligence</span>, <span className="text-primary font-bold">Execution</span>, and <span className="text-primary font-bold">Analytics</span> clusters.
                  </p>
                  <div className="p-6 rounded-2xl bg-primary/5 border border-primary/10 space-y-4">
                    <div className="flex items-center gap-3">
                      <Database size={18} className="text-primary" />
                      <span className="text-xs font-black uppercase tracking-tight">Immutable Audit Trail</span>
                    </div>
                    <p className="text-[10px] text-text-secondary leading-relaxed font-medium uppercase">Every action in this terminal is logged to an ISO-27001 compliant audit trail for institutional transparency.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">Back</Button>
                  <Button onClick={handleNext} className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs">Final Compliance</Button>
                </div>
              </div>
            )}

            {step === 6 && (
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4">
                    <Scale size={24} />
                  </div>
                  <h2 className="text-xl font-black uppercase tracking-tight">Compliance & Data Privacy</h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    AlphaForge requires mandatory consent for GDPR/CCPA data handling. We encrypt all institutional PII at rest.
                  </p>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-start gap-3 p-4 rounded-xl bg-elevated/20 border border-border-subtle">
                      <Checkbox id="gdpr" checked={gdpr} onCheckedChange={(v) => setGdpr(v as boolean)} className="mt-1" />
                      <Label htmlFor="gdpr" className="text-[10px] font-bold text-text-muted uppercase leading-snug cursor-pointer">
                        I acknowledge the data retention policies and consent to high-frequency telemetry processing for institutional reporting.
                      </Label>
                    </div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">Back</Button>
                  <Button 
                    onClick={handleCompleteOnboarding}
                    disabled={!gdpr || isSubmitting}
                    className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : "Initialize Terminal"}
                  </Button>
                </div>
              </div>
            )}
          </SpotlightCard>
        </div>

        <p className="text-center text-[10px] text-text-muted uppercase font-black tracking-widest opacity-50">
          Session ID: {user?.uid.slice(0, 12)}... | AlphaForge Core v1.0.8
        </p>
      </div>
    </div>
  );
}