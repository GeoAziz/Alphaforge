'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export function RiskSettings() {
  const [riskLevel, setRiskLevel] = useState('balanced');
  const [positionSize, setPositionSize] = useState(2.5);
  const [maxDrawdown, setMaxDrawdown] = useState(15);

  return (
    <SpotlightCard className="p-8">
      <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
        <AlertTriangle size={18} className="text-amber" />
        Risk Management
      </h3>

      <div className="space-y-8">
        <div>
          <Label className="text-xs font-black uppercase mb-4 block">Risk Profile</Label>
          <RadioGroup value={riskLevel} onValueChange={setRiskLevel}>
            <div className="space-y-3">
              <div className="flex items-center p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-pointer">
                <RadioGroupItem value="conservative" id="conservative" className="mr-3" />
                <Label htmlFor="conservative" className="flex-1 cursor-pointer">
                  <div className="font-bold text-text-primary">Conservative</div>
                  <div className="text-[10px] text-text-muted">Priority on capital preservation</div>
                </Label>
              </div>
              <div className="flex items-center p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-pointer">
                <RadioGroupItem value="balanced" id="balanced" className="mr-3" />
                <Label htmlFor="balanced" className="flex-1 cursor-pointer">
                  <div className="font-bold text-text-primary">Balanced</div>
                  <div className="text-[10px] text-text-muted">Moderate growth with controlled exposure</div>
                </Label>
              </div>
              <div className="flex items-center p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all cursor-pointer">
                <RadioGroupItem value="aggressive" id="aggressive" className="mr-3" />
                <Label htmlFor="aggressive" className="flex-1 cursor-pointer">
                  <div className="font-bold text-text-primary">Aggressive</div>
                  <div className="text-[10px] text-text-muted">High-frequency alpha pursuit</div>
                </Label>
              </div>
            </div>
          </RadioGroup>
        </div>

        <div className="pt-6 border-t border-border-subtle">
          <Label className="text-xs font-black uppercase mb-4 block">Position Size Limit (%)</Label>
          <div className="flex items-center gap-4">
            <Slider 
              value={[positionSize]}
              onValueChange={(value) => setPositionSize(value[0])}
              min={0.5}
              max={10}
              step={0.5}
              className="flex-1"
            />
            <span className="text-lg font-black font-mono text-primary w-12 text-right">{positionSize.toFixed(1)}%</span>
          </div>
        </div>

        <div className="pt-6 border-t border-border-subtle">
          <Label className="text-xs font-black uppercase mb-4 block">Maximum Drawdown Threshold (%)</Label>
          <div className="flex items-center gap-4">
            <Slider 
              value={[maxDrawdown]}
              onValueChange={(value) => setMaxDrawdown(value[0])}
              min={5}
              max={50}
              step={5}
              className="flex-1"
            />
            <span className="text-lg font-black font-mono text-red w-12 text-right">{maxDrawdown}%</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-red/5 border border-red/20">
          <div className="text-[10px] font-bold text-red uppercase">Risk Warning</div>
          <div className="text-xs text-red/80 mt-2">Aggressive settings increase your portfolio's volatility and potential for significant losses.</div>
        </div>
      </div>
    </SpotlightCard>
  );
}
