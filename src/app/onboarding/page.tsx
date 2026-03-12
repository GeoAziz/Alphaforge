'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, useFirestore, useDoc, useMemoFirebase } from '@/firebase';
import { doc } from 'firebase/firestore';
import { setDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowRight, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

// Step Components
import { OnboardingStepper } from '@/components/onboarding/onboarding-stepper';
import { StepAccount } from '@/components/onboarding/step-account';
import { StepExchange } from '@/components/onboarding/step-exchange';
import { StepRisk } from '@/components/onboarding/step-risk';
import { StepNotifications } from '@/components/onboarding/step-notifications';
import { StepWalkthrough } from '@/components/onboarding/step-walkthrough';
import { StepPaperTradeGate } from '@/components/onboarding/step-paper-trade-gate';
import { StepRegulatoryConsent } from '@/components/onboarding/step-regulatory-consent';

export default function OnboardingPage() {
  const { user, isUserLoading } = useUser();
  const db = useFirestore();
  const router = useRouter();
  
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState<'next' | 'back'>('next');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // State for aggregate onboarding data
  const [formData, setFormData] = useState({
    name: '',
    risk: 'balanced',
    notificationPrefs: { signals: true, trades: true, risk: true, system: false },
    gdpr: false,
    ccpa: false,
    disclaimer: false
  });

  const profileRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid);
  }, [user, db]);

  const { data: profile, isLoading: isProfileLoading } = useDoc(profileRef);

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

  function handleComplete() {
    if (!profileRef || !user) return;
    setIsSubmitting(true);

    const onboardingData = {
      id: user.uid,
      name: formData.name || 'Institutional Node',
      email: user.email || '',
      plan: 'free',
      riskTolerance: formData.risk,
      onboardingComplete: true,
      paperTradingStartDate: new Date().toISOString(),
      createdAt: new Date().toISOString(),
    };

    setDocumentNonBlocking(profileRef, onboardingData, { merge: true });
    
    setTimeout(() => {
      router.push('/');
    }, 1000);
  }

  if (isUserLoading || isProfileLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  const totalSteps = 7; // Including 5A (Paper Trade Gate)

  return (
    <div className="h-screen w-full flex items-center justify-center bg-background p-6 overflow-hidden">
      <div className="max-w-2xl w-full space-y-8 animate-page">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary mb-4 font-black text-primary-foreground shadow-[0_0_20px_rgba(96,165,250,0.4)]">
            AF
          </div>
          <h1 className="text-4xl font-black uppercase tracking-tighter">Terminal Initialization</h1>
          <div className="pt-4 max-w-sm mx-auto">
            <OnboardingStepper currentStep={step} totalSteps={totalSteps} />
          </div>
        </div>

        <SpotlightCard className="p-10 shadow-2xl border-primary/10 bg-surface/50 backdrop-blur-xl">
          <div className="min-h-[400px] flex flex-col justify-between gap-10">
            <div className="flex-1">
              {step === 1 && (
                <StepAccount 
                  name={formData.name} 
                  onNameChange={(v) => setFormData(prev => ({ ...prev, name: v }))} 
                />
              )}
              {step === 2 && <StepExchange />}
              {step === 3 && (
                <StepRisk 
                  risk={formData.risk} 
                  onRiskChange={(v) => setFormData(prev => ({ ...prev, risk: v }))} 
                />
              )}
              {step === 4 && (
                <StepNotifications 
                  prefs={formData.notificationPrefs} 
                  onChange={(k, v) => setFormData(prev => ({ ...prev, notificationPrefs: { ...prev.notificationPrefs, [k]: v } }))} 
                />
              )}
              {step === 5 && <StepWalkthrough />}
              {step === 6 && <StepPaperTradeGate />}
              {step === 7 && (
                <StepRegulatoryConsent 
                  gdprAccepted={formData.gdpr}
                  ccpaAccepted={formData.ccpa}
                  disclaimerAccepted={formData.disclaimer}
                  onGdprChange={(v) => setFormData(prev => ({ ...prev, gdpr: v }))}
                  onCcpaChange={(v) => setFormData(prev => ({ ...prev, ccpa: v }))}
                  onDisclaimerChange={(v) => setFormData(prev => ({ ...prev, disclaimer: v }))}
                />
              )}
            </div>

            <div className="flex gap-4 pt-6 border-t border-border-subtle">
              {step > 1 && (
                <Button variant="ghost" onClick={handleBack} className="flex-1 h-14 font-black uppercase text-xs">
                  <ArrowLeft size={16} className="mr-2" /> Back
                </Button>
              )}
              
              {step < totalSteps ? (
                <Button 
                  onClick={handleNext}
                  disabled={step === 1 && !formData.name}
                  className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 group"
                >
                  Continue Traversal <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </Button>
              ) : (
                <Button 
                  onClick={handleComplete}
                  disabled={!formData.gdpr || !formData.ccpa || !formData.disclaimer || isSubmitting}
                  className="flex-[2] h-14 bg-primary text-primary-foreground font-black uppercase text-xs gap-2 shadow-[0_0_20px_rgba(96,165,250,0.4)]"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : "Initialize Node Cluster"}
                </Button>
              )}
            </div>
          </div>
        </SpotlightCard>

        <p className="text-center text-[10px] text-text-muted uppercase font-black tracking-widest opacity-50">
          Handshake Frequency: 14.2 GHz | AlphaForge Core v1.0.8
        </p>
      </div>
    </div>
  );
}
