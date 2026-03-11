
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
import { Loader2, ArrowRight, ShieldCheck, Zap, TrendingUp } from 'lucide-react';
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
  const [name, setName] = useState('');
  const [risk, setRisk] = useState('balanced');
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
    
    // Immediate redirect for best UX
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
    <div className="h-screen w-full flex items-center justify-center bg-background p-6">
      <div className="max-w-2xl w-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary mb-4 font-black text-primary-foreground shadow-[0_0_20px_rgba(96,165,250,0.4)]">
            AF
          </div>
          <h1 className="text-4xl font-black uppercase tracking-tighter">Terminal Initialization</h1>
          <p className="text-text-muted text-sm uppercase tracking-widest font-bold">Step {step} of 2</p>
        </div>

        <SpotlightCard className="p-10 shadow-2xl border-primary/10 bg-surface/50 backdrop-blur-xl">
          {step === 1 ? (
            <div className="space-y-8">
              <div className="space-y-4">
                <h2 className="text-xl font-black uppercase tracking-tight">Identity Handshake</h2>
                <p className="text-sm text-text-muted leading-relaxed">
                  AlphaForge requires a node identifier for session persistence and institutional reporting.
                </p>
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase text-text-muted">Display Name</Label>
                  <Input 
                    value={name} 
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your node identifier..."
                    className="h-14 bg-elevated/50 border-border-subtle focus:ring-primary/20"
                  />
                </div>
              </div>
              <Button 
                onClick={() => setStep(2)}
                disabled={!name}
                className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 group"
              >
                Configure Risk Profile <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
          ) : (
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
                          <div className="text-[11px] text-text-muted leading-snug">{level.description}</div>
                        </div>
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
              <div className="flex gap-4">
                <Button 
                  variant="ghost"
                  onClick={() => setStep(1)}
                  className="flex-1 h-14 font-black uppercase text-xs"
                >
                  Back
                </Button>
                <Button 
                  onClick={handleCompleteOnboarding}
                  disabled={isSubmitting}
                  className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : "Finalize Handshake"}
                </Button>
              </div>
            </div>
          )}
        </SpotlightCard>

        <p className="text-center text-[10px] text-text-muted uppercase font-black tracking-widest opacity-50">
          Encrypted Session ID: {user?.uid.slice(0, 12)}...
        </p>
      </div>
    </div>
  );
}
