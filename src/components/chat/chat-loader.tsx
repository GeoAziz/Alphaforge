'use client';

import { Bot } from 'lucide-react';

export function ChatLoader() {
  return (
    <div className="flex w-full gap-3 mb-4 animate-in fade-in duration-300">
      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shrink-0">
        <Bot size={16} />
      </div>
      <div className="space-y-2">
        <div className="p-4 rounded-2xl bg-elevated/30 border border-border-subtle text-text-muted rounded-tl-none">
          <div className="flex gap-1">
            <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" />
            <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce delay-150" />
            <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce delay-300" />
          </div>
        </div>
        <div className="text-[8px] font-black text-primary uppercase tracking-widest px-1 animate-pulse">
          Synthesizing Alpha...
        </div>
      </div>
    </div>
  );
}
