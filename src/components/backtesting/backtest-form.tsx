
'use client';

import { useState } from 'react';
import { Strategy } from '@/lib/types';
import { Settings2, Play, Loader2, Calendar, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { SpotlightCard } from '@/components/shared/spotlight-card';

interface BacktestFormProps {
  strategies: Strategy[] | null;
  onRun: (config: any) => void;
  isLoading: boolean;
}

export function BacktestForm({ strategies, onRun, isLoading }: BacktestFormProps) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [risk, setRisk] = useState(2.5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStrategy) return;
    onRun({ strategyId: selectedStrategy, risk });
  };

  return (
    <SpotlightCard className="p-6 space-y-8 border-primary/10">
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="space-y-6">
          <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
            <Settings2 size={16} className="text-primary" />
            Parameter Config
          </h3>
          
          <div className="space-y-2">
            <Label className="text-[10px] font-black uppercase text-text-muted">Algorithm Selection</Label>
            <Select onValueChange={setSelectedStrategy}>
              <SelectTrigger className="bg-elevated/50 border-border-subtle h-12 text-xs font-bold uppercase">
                <SelectValue placeholder="Select Strategy Cluster" />
              </SelectTrigger>
              <SelectContent className="glass">
                {strategies?.map(s => (
                  <SelectItem key={s.id} value={s.id} className="font-bold uppercase text-[10px]">{s.name}</SelectItem>
                ))}
                <SelectItem value="default" className="font-bold text-text-muted italic text-[10px]">Momentum Alpha Core</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase text-text-muted">Asset Cluster</Label>
              <Select defaultValue="BTCUSDT">
                <SelectTrigger className="bg-elevated/50 border-border-subtle h-12 text-xs font-bold uppercase">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="glass">
                  <SelectItem value="BTCUSDT" className="text-[10px] font-black">BTC/USDT</SelectItem>
                  <SelectItem value="ETHUSDT" className="text-[10px] font-black">ETH/USDT</SelectItem>
                  <SelectItem value="SOLUSDT" className="text-[10px] font-black">SOL/USDT</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase text-text-muted">Resolution</Label>
              <Select defaultValue="1h">
                <SelectTrigger className="bg-elevated/50 border-border-subtle h-12 text-xs font-bold uppercase">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="glass">
                  <SelectItem value="15m" className="text-[10px] font-black">15 Minutes</SelectItem>
                  <SelectItem value="1h" className="text-[10px] font-black">1 Hour</SelectItem>
                  <SelectItem value="4h" className="text-[10px] font-black">4 Hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-[10px] font-black uppercase text-text-muted">Initial Capital</Label>
                <span className="text-xs font-bold text-primary font-mono">$10,000.00</span>
              </div>
              <Input type="number" defaultValue={10000} className="bg-elevated/30 border-border-subtle h-12 font-mono font-bold" />
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-[10px] font-black uppercase text-text-muted">Risk Per Trade</Label>
                <span className="text-xs font-bold text-primary font-mono">{risk}%</span>
              </div>
              <Slider value={[risk]} onValueChange={([v]) => setRisk(v)} max={10} step={0.1} />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-3">
            <div className="flex items-center gap-2 text-primary">
              <Calendar size={14} />
              <span className="text-[10px] font-black uppercase tracking-widest">Historical Window</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-[8px] font-bold text-text-muted uppercase">Start Date</Label>
                <Input type="date" defaultValue="2024-01-01" className="h-8 bg-surface text-[10px] uppercase font-bold border-none" />
              </div>
              <div className="space-y-1">
                <Label className="text-[8px] font-bold text-text-muted uppercase">End Date</Label>
                <Input type="date" defaultValue="2024-03-01" className="h-8 bg-surface text-[10px] uppercase font-bold border-none" />
              </div>
            </div>
          </div>
        </div>

        <Button 
          type="submit"
          disabled={isLoading || !selectedStrategy}
          className="w-full h-14 bg-primary text-primary-foreground font-black uppercase text-xs rounded-2xl shadow-lg gap-2 group"
        >
          {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} className="group-hover:scale-110 transition-transform" />}
          Execute Historical Simulation
        </Button>
      </form>
    </SpotlightCard>
  );
}
