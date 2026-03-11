'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { BookOpen } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export function StepWalkthrough() {
  const features = [
    { title: 'Dashboard Overview', description: 'Real-time portfolio metrics and signal stream' },
    { title: 'Signal Execution', description: 'Execute institutional-grade trading signals with one click' },
    { title: 'Portfolio Management', description: 'Track positions, trades, and performance metrics' },
    { title: 'Risk Controls', description: 'Audit trail of all trades and margin calculations pre-verified' },
    { title: 'Advanced Analytics', description: 'Deep dive into strategy performance and market intelligence' },
  ];

  return (
    <SpotlightCard className="p-8 max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <BookOpen size={24} className="text-primary" />
        <h2 className="text-2xl font-black uppercase tracking-tight">Platform Walkthrough</h2>
      </div>

      <p className="text-text-secondary text-sm mb-8">Get familiar with AlphaForge's core features:</p>

      <div className="space-y-3">
        {features.map((feature, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <div className="flex items-center justify-between mb-2">
              <div className="font-bold text-text-primary">{feature.title}</div>
              <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px]">{idx + 1}</Badge>
            </div>
            <div className="text-[11px] text-text-secondary">{feature.description}</div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 rounded-xl bg-primary/5 border border-primary/20">
        <div className="text-[10px] font-bold text-primary uppercase mb-2">Pro Tip</div>
        <div className="text-[10px] text-primary/80">
          Use the command palette (⌘K) to quickly navigate between pages and search for signals, positions, and settings.
        </div>
      </div>
    </SpotlightCard>
  );
}
