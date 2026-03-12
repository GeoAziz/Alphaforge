'use client';

import { Search, Filter, SlidersHorizontal, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SignalFiltersProps {
  search: string;
  onSearchChange: (val: string) => void;
  strategy: string;
  onStrategyChange: (val: string) => void;
  status: string;
  onStatusChange: (val: string) => void;
  confidence: number;
  onConfidenceChange: (val: number) => void;
  onClear: () => void;
}

export function SignalFilters({
  search, onSearchChange,
  strategy, onStrategyChange,
  status, onStatusChange,
  confidence, onConfidenceChange,
  onClear
}: SignalFiltersProps) {
  const isFiltered = search !== "" || strategy !== "all" || status !== "active" || confidence > 0;

  return (
    <div className="bg-elevated/20 p-4 rounded-2xl border border-border-subtle flex flex-col lg:flex-row items-center gap-4 backdrop-blur-xl">
      <div className="relative flex-1 w-full">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <Input 
          placeholder="Filter Intelligence Clusters..." 
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10 h-12 bg-surface/50 border-border-subtle text-xs font-bold uppercase"
        />
      </div>

      <div className="flex items-center gap-3 w-full lg:w-auto overflow-x-auto scrollbar-hide pb-1 lg:pb-0">
        <Select value={status} onValueChange={onStatusChange}>
          <SelectTrigger className="w-[140px] h-12 bg-surface/50 border-border-subtle text-[10px] font-black uppercase">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent className="glass border-border-subtle">
            <SelectItem value="active" className="text-[10px] font-black uppercase">Active Nodes</SelectItem>
            <SelectItem value="closed" className="text-[10px] font-black uppercase">Resolved</SelectItem>
            <SelectItem value="all" className="text-[10px] font-black uppercase">All Streams</SelectItem>
          </SelectContent>
        </Select>

        <Select value={strategy} onValueChange={onStrategyChange}>
          <SelectTrigger className="w-[160px] h-12 bg-surface/50 border-border-subtle text-[10px] font-black uppercase">
            <SelectValue placeholder="Strategy Cluster" />
          </SelectTrigger>
          <SelectContent className="glass border-border-subtle">
            <SelectItem value="all" className="text-[10px] font-black uppercase">All Algorithms</SelectItem>
            <SelectItem value="Momentum Breakout" className="text-[10px] font-black uppercase">Momentum</SelectItem>
            <SelectItem value="Mean Reversion" className="text-[10px] font-black uppercase">Mean Reversion</SelectItem>
            <SelectItem value="Volatility Expansion" className="text-[10px] font-black uppercase">Volatility</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex flex-col gap-1 px-4 min-w-[180px]">
          <div className="flex justify-between text-[8px] font-black uppercase text-text-muted">
            <span>Min Confidence</span>
            <span className="text-primary">{confidence}%</span>
          </div>
          <Slider 
            value={[confidence]} 
            onValueChange={(v) => onConfidenceChange(v[0])} 
            max={100} 
            step={5} 
            className="w-full"
          />
        </div>

        {isFiltered && (
          <Button 
            variant="ghost" 
            onClick={onClear}
            className="h-12 px-4 text-red font-black uppercase text-[10px] gap-2 hover:bg-red/5"
          >
            <X size={14} /> Reset
          </Button>
        )}
      </div>
    </div>
  );
}
