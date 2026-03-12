'use client';

import { useState } from 'react';
import { SignalIngestionRule } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SlidersHorizontal, ShieldCheck, Save, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface IngestionRulesPanelProps {
  initialRule: SignalIngestionRule;
}

export function IngestionRulesPanel({ initialRule }: IngestionRulesPanelProps) {
  const [rule, setRule] = useState(initialRule);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      toast({
        title: "Rules Calibrated",
        description: "Institutional ingestion parameters updated successfully.",
      });
    }, 1000);
  };

  return (
    <SpotlightCard className="p-8 border-primary/10">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
          <SlidersHorizontal size={16} className="text-primary" />
          Ingestion Rules Engine
        </h3>
        <Button 
          size="sm" 
          onClick={handleSave} 
          disabled={isSaving}
          className="h-9 px-6 bg-primary text-primary-foreground font-black uppercase text-[10px] gap-2 rounded-lg"
        >
          {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          Commit Rules
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
        {/* Signal Filters */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase text-text-primary tracking-widest pb-2 border-b border-border-subtle">
            <ShieldCheck size={14} className="text-green" /> Signal Filters
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label className="text-[9px] font-black uppercase text-text-muted">Min Confidence</Label>
              <span className="text-xs font-bold text-primary">{rule.minConfidence}%</span>
            </div>
            <Slider 
              value={[rule.minConfidence]} 
              onValueChange={([v]) => setRule(prev => ({...prev, minConfidence: v}))}
              max={100} 
              step={5} 
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl bg-elevated/20 border border-border-subtle">
            <div className="space-y-0.5">
              <Label htmlFor="auto-exec" className="text-[10px] font-black uppercase cursor-pointer">Auto-Execute</Label>
              <p className="text-[8px] font-bold text-text-muted uppercase">Sync directly to exchange</p>
            </div>
            <Switch 
              id="auto-exec" 
              checked={rule.autoExecute}
              onCheckedChange={(v) => setRule(prev => ({...prev, autoExecute: v}))}
            />
          </div>
        </div>

        {/* Risk Controls */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase text-text-primary tracking-widest pb-2 border-b border-border-subtle">
            <ShieldCheck size={14} className="text-amber" /> Risk Controls
          </div>

          <div className="space-y-2">
            <Label className="text-[9px] font-black uppercase text-text-muted">Max Concurrent Nodes</Label>
            <Input 
              type="number" 
              value={rule.maxPositionsOpen}
              onChange={(e) => setRule(prev => ({...prev, maxPositionsOpen: parseInt(e.target.value)}))}
              className="bg-elevated/30 border-border-subtle h-10 font-bold"
            />
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label className="text-[9px] font-black uppercase text-text-muted">Risk Multiplier</Label>
              <span className="text-xs font-bold text-amber">{rule.riskMultiplier}x</span>
            </div>
            <Slider 
              value={[rule.riskMultiplier * 10]} 
              onValueChange={([v]) => setRule(prev => ({...prev, riskMultiplier: v / 10}))}
              max={20} 
              step={1} 
            />
          </div>
        </div>

        {/* Temporal Rules */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase text-text-primary tracking-widest pb-2 border-b border-border-subtle">
            <ShieldCheck size={14} className="text-primary" /> Temporal Rules
          </div>

          <div className="space-y-2">
            <Label className="text-[9px] font-black uppercase text-text-muted">Ingestion Cooldown</Label>
            <Select 
              value={rule.cooldownSeconds.toString()} 
              onValueChange={(v) => setRule(prev => ({...prev, cooldownSeconds: parseInt(v)}))}
            >
              <SelectTrigger className="bg-elevated/30 border-border-subtle h-10 text-[10px] font-black uppercase">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="glass">
                <SelectItem value="30">30 Seconds</SelectItem>
                <SelectItem value="60">1 Minute</SelectItem>
                <SelectItem value="300">5 Minutes</SelectItem>
                <SelectItem value="900">15 Minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
