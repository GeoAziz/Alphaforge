'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { AlertTriangle, ShieldAlert, Zap, TrendingUp, Info } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { RiskScore } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";

export function RiskSettings() {
  const [riskLevel, setRiskLevel] = useState('balanced');
  const [positionSize, setPositionSize] = useState(2.5);
  const [maxLeverage, setMaxLeverage] = useState(5);
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);

  useEffect(() => {
    api.user.getRiskScore('current').then(setRiskScore);
  }, []);

  return (
    <div className="space-y-8">
      {/* Risk Score Display */}
      <SpotlightCard className="p-8 border-primary/10 bg-primary/5">
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-1">
            <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary">
              <ShieldAlert size={20} className="text-primary" />
              Institutional Risk Node
            </h3>
            <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Aggregate portfolio exposure analysis</p>
          </div>
          <Badge variant="outline" className="text-[10px] font-black uppercase border-primary/20 text-primary">Live Scan</Badge>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-12">
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg className="w-full h-full rotate-[-90deg]">
              <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-border-subtle" />
              <circle 
                cx="64" 
                cy="64" 
                r="58" 
                stroke="currentColor" 
                strokeWidth="8" 
                fill="transparent" 
                className={cn(
                  "transition-all duration-1000 ease-out",
                  riskScore && riskScore.score < 30 ? "text-green" : riskScore && riskScore.score < 60 ? "text-amber" : "text-red"
                )}
                strokeDasharray="364.4" 
                strokeDashoffset={364.4 - (364.4 * (riskScore?.score || 0) / 100)} 
                strokeLinecap="round" 
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-black tracking-tighter">{riskScore?.score || '--'}</span>
              <span className="text-[8px] font-black uppercase text-text-muted tracking-widest">{riskScore?.label || 'Calculating'}</span>
            </div>
          </div>

          <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-6 w-full">
            {[
              { label: 'Volatility', value: riskScore?.factors.volatility || 0, color: 'text-primary' },
              { label: 'Leverage', value: riskScore?.factors.leverage || 0, color: 'text-accent' },
              { label: 'Concentration', value: riskScore?.factors.concentration || 0, color: 'text-amber' },
            ].map(f => (
              <div key={f.label} className="space-y-2 p-4 rounded-xl bg-surface/50 border border-border-subtle">
                <div className="text-[9px] font-black uppercase text-text-muted tracking-widest">{f.label}</div>
                <div className={cn("text-xl font-black font-mono", f.color)}>{f.value}%</div>
                <div className="h-1 bg-elevated rounded-full overflow-hidden">
                  <div className={cn("h-full", f.color.replace('text-', 'bg-'))} style={{ width: `${f.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </SpotlightCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <SpotlightCard className="p-8 space-y-8">
          <div>
            <Label className="text-xs font-black uppercase mb-6 block text-text-muted tracking-widest">Institutional Risk Profile</Label>
            <RadioGroup value={riskLevel} onValueChange={setRiskLevel} className="grid grid-cols-1 gap-4">
              <div className={cn(
                "flex items-center p-5 rounded-2xl border transition-all cursor-pointer group",
                riskLevel === 'conservative' ? "bg-primary/5 border-primary/30 shadow-[0_0_20px_rgba(96,165,250,0.1)]" : "bg-elevated/20 border-border-subtle hover:bg-elevated/40"
              )}>
                <RadioGroupItem value="conservative" id="conservative" className="sr-only" />
                <Label htmlFor="conservative" className="flex items-start gap-4 flex-1 cursor-pointer">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center border", riskLevel === 'conservative' ? "bg-primary text-primary-foreground border-primary/20" : "bg-surface text-text-muted border-border-subtle")}>
                    <ShieldCheck size={20} />
                  </div>
                  <div className="space-y-1">
                    <div className="font-black text-sm uppercase tracking-tight">Conservative</div>
                    <div className="text-[10px] text-text-muted uppercase font-bold leading-snug">Priority on capital preservation. 1% max position.</div>
                  </div>
                </Label>
              </div>
              
              <div className={cn(
                "flex items-center p-5 rounded-2xl border transition-all cursor-pointer group",
                riskLevel === 'balanced' ? "bg-primary/5 border-primary/30 shadow-[0_0_20px_rgba(96,165,250,0.1)]" : "bg-elevated/20 border-border-subtle hover:bg-elevated/40"
              )}>
                <RadioGroupItem value="balanced" id="balanced" className="sr-only" />
                <Label htmlFor="balanced" className="flex items-start gap-4 flex-1 cursor-pointer">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center border", riskLevel === 'balanced' ? "bg-primary text-primary-foreground border-primary/20" : "bg-surface text-text-muted border-border-subtle")}>
                    <Zap size={20} />
                  </div>
                  <div className="space-y-1">
                    <div className="font-black text-sm uppercase tracking-tight">Balanced</div>
                    <div className="text-[10px] text-text-muted uppercase font-bold leading-snug">Institutional 2.5% risk parity standard.</div>
                  </div>
                </Label>
              </div>

              <div className={cn(
                "flex items-center p-5 rounded-2xl border transition-all cursor-pointer group",
                riskLevel === 'aggressive' ? "bg-primary/5 border-primary/30 shadow-[0_0_20px_rgba(96,165,250,0.1)]" : "bg-elevated/20 border-border-subtle hover:bg-elevated/40"
              )}>
                <RadioGroupItem value="aggressive" id="aggressive" className="sr-only" />
                <Label htmlFor="aggressive" className="flex items-start gap-4 flex-1 cursor-pointer">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center border", riskLevel === 'aggressive' ? "bg-primary text-primary-foreground border-primary/20" : "bg-surface text-text-muted border-border-subtle")}>
                    <TrendingUp size={20} />
                  </div>
                  <div className="space-y-1">
                    <div className="font-black text-sm uppercase tracking-tight">Aggressive</div>
                    <div className="text-[10px] text-text-muted uppercase font-bold leading-snug">Alpha pursuit with 5% max exposure.</div>
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-8 space-y-10">
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <Label className="text-xs font-black uppercase text-text-muted tracking-widest">Position Resolution Limit</Label>
              <span className="text-lg font-black font-mono text-primary">{positionSize.toFixed(1)}%</span>
            </div>
            <Slider 
              value={[positionSize]}
              onValueChange={(value) => setPositionSize(value[0])}
              min={0.5}
              max={10}
              step={0.5}
            />
            <p className="text-[10px] text-text-muted uppercase font-bold leading-relaxed">System-wide cap on any single algorithmic resolution.</p>
          </div>

          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <Label className="text-xs font-black uppercase text-text-muted tracking-widest flex items-center gap-2">
                Perpetuals Leverage Tier
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button><Info size={14} className="text-text-muted hover:text-primary transition-colors" /></button>
                    </TooltipTrigger>
                    <TooltipContent className="glass border-border-subtle p-3 max-w-[200px]">
                      <p className="text-[10px] font-bold uppercase leading-relaxed">Higher leverage tiers reduce the liquidation buffer and increase protocol risk.</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <span className={cn(
                "text-lg font-black font-mono",
                maxLeverage <= 5 ? "text-green" : maxLeverage <= 10 ? "text-amber" : "text-red"
              )}>{maxLeverage}x</span>
            </div>
            <Slider 
              value={[maxLeverage]}
              onValueChange={(v) => setMaxLeverage(v[0])}
              min={1}
              max={20}
              step={1}
            />
            
            <div className={cn(
              "p-4 rounded-xl border flex items-start gap-3 transition-all",
              maxLeverage <= 5 ? "bg-green/5 border-green/20" : maxLeverage <= 10 ? "bg-amber/5 border-amber/20" : "bg-red/5 border-red/20"
            )}>
              <ShieldAlert size={16} className={cn("mt-0.5 shrink-0", maxLeverage > 10 ? "text-red" : "text-text-muted")} />
              <div className="space-y-1">
                <div className="text-[10px] font-black uppercase text-text-primary">Liquidation Buffer Node</div>
                <p className="text-[9px] font-bold text-text-muted uppercase leading-relaxed">
                  At {maxLeverage}x leverage, a { (100/maxLeverage).toFixed(1) }% move against position will result in total node liquidation.
                </p>
              </div>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
