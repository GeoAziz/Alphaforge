'use client';

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { ShieldCheck, Zap, TrendingUp, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

const RISK_LEVELS = [
  { id: 'conservative', label: 'Conservative', description: 'Capital preservation node. 1% max exposure per resolution.', icon: ShieldCheck, color: 'text-green' },
  { id: 'balanced', label: 'Balanced', description: 'Moderate growth cluster. 2.5% risk parity settings.', icon: Zap, color: 'text-primary' },
  { id: 'aggressive', label: 'Aggressive', description: 'High-frequency alpha pursuit. 5% max exposure limits.', icon: TrendingUp, color: 'text-red' },
];

interface StepRiskProps {
  risk: string;
  onRiskChange: (val: string) => void;
}

export function StepRisk({ risk, onRiskChange }: StepRiskProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 mb-6">
          <ShieldAlert size={24} />
        </div>
        <h2 className="text-2xl font-black uppercase tracking-tight">Regime Sensitivity</h2>
        <p className="text-sm text-text-muted leading-relaxed">
          Select your institutional risk tolerance. This calibrates signal filtering, margin exposure alerts, and algorithmic damping.
        </p>
      </div>

      <RadioGroup value={risk} onValueChange={onRiskChange} className="grid grid-cols-1 gap-4">
        {RISK_LEVELS.map((level) => (
          <div key={level.id}>
            <RadioGroupItem value={level.id} id={level.id} className="peer sr-only" />
            <Label
              htmlFor={level.id}
              className={cn(
                "flex items-start gap-4 p-5 rounded-xl border border-border-subtle bg-elevated/20 cursor-pointer transition-all hover:bg-elevated/40 peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5",
                risk === level.id && "border-primary bg-primary/5"
              )}
            >
              <div className={cn(
                "mt-1 w-10 h-10 rounded-lg flex items-center justify-center",
                risk === level.id ? "bg-primary text-primary-foreground shadow-[0_0_15px_rgba(96,165,250,0.3)]" : "bg-elevated text-text-muted"
              )}>
                <level.icon size={20} />
              </div>
              <div className="space-y-1 flex-1">
                <div className="flex justify-between items-center">
                  <div className="font-black text-sm uppercase tracking-tight">{level.label}</div>
                  {risk === level.id && <div className="text-[8px] font-black text-primary uppercase border border-primary/30 px-1.5 rounded">Active Node</div>}
                </div>
                <div className="text-[11px] text-text-muted leading-snug font-medium uppercase">{level.description}</div>
              </div>
            </Label>
          </div>
        ))}
      </RadioGroup>

      <div className="p-4 rounded-xl bg-red/5 border border-red/10 space-y-3">
        <div className="flex items-center gap-2 text-red">
          <ShieldAlert size={14} />
          <span className="text-[10px] font-black uppercase tracking-widest">Institutional Disclaimer</span>
        </div>
        <p className="text-[9px] text-text-muted font-bold uppercase leading-relaxed">
          Past performance is not indicative of future alpha. Your risk settings control position sizing only and do not constitute financial advice. Consult a licensed adviser before trading real capital.
        </p>
      </div>
    </div>
  );
}
