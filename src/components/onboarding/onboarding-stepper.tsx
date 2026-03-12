'use client';

import { cn } from "@/lib/utils";

interface OnboardingStepperProps {
  currentStep: number;
  totalSteps: number;
}

/**
 * OnboardingStepper - Institutional progress telemetry.
 */
export function OnboardingStepper({ currentStep, totalSteps }: OnboardingStepperProps) {
  const steps = [
    "Identity",
    "Handshake",
    "Risk",
    "Alerts",
    "Walkthrough",
    "Consent"
  ];

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-black uppercase text-primary tracking-widest">Initialization Node</span>
        <span className="text-[10px] font-black uppercase text-text-muted">Step {currentStep} of {totalSteps}</span>
      </div>
      <div className="flex gap-2">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div 
            key={i} 
            className={cn(
              "h-1.5 flex-1 rounded-full transition-all duration-700 relative",
              i + 1 === currentStep ? "bg-primary shadow-[0_0_15px_rgba(96,165,250,0.6)]" : i + 1 < currentStep ? "bg-primary/40" : "bg-elevated"
            )}
          >
            {i + 1 === currentStep && (
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[8px] font-black uppercase text-primary whitespace-nowrap animate-in fade-in zoom-in-95">
                {steps[i]}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
