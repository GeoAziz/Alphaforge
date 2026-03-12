'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Brain, Info } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";

export function MarketSentimentCell() {
  const sentimentScore = 72; // Greed
  const label = 'Greed';

  return (
    <SpotlightCard className="p-8 h-full flex flex-col justify-between">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-text-primary">
          <Brain size={16} className="text-primary" />
          Sentiment Gauge
        </h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="text-text-muted hover:text-text-primary transition-colors">
                <Info size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent className="glass max-w-xs p-3">
              <p className="text-[10px] font-bold uppercase leading-relaxed">
                NLP-derived analysis of global institutional order flows and social momentum nodes.
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="flex flex-col items-center justify-center py-4">
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
              className="text-primary transition-all duration-1000 ease-out" 
              strokeDasharray="364.4" 
              strokeDashoffset={364.4 - (364.4 * sentimentScore / 100)} 
              strokeLinecap="round" 
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-black tracking-tighter">{sentimentScore}</span>
            <span className="text-[8px] font-black uppercase text-primary tracking-widest">{label}</span>
          </div>
        </div>
      </div>

      <div className="space-y-4 mt-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
            <span>Social Momentum</span>
            <span className="text-text-primary">84%</span>
          </div>
          <Progress value={84} className="h-1 bg-border-subtle" />
        </div>
        <div className="space-y-1.5">
          <div className="flex justify-between text-[9px] font-black uppercase text-text-muted">
            <span>Volatility Regime</span>
            <span className="text-green">Low</span>
          </div>
          <Progress value={22} className="h-1 bg-border-subtle" />
        </div>
      </div>
    </SpotlightCard>
  );
}