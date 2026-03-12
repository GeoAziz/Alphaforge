'use client';

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ShieldCheck } from "lucide-react";

interface StepAccountProps {
  name: string;
  onNameChange: (val: string) => void;
}

export function StepAccount({ name, onNameChange }: StepAccountProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 mb-6">
          <ShieldCheck size={24} />
        </div>
        <h2 className="text-2xl font-black uppercase tracking-tight">Identity Handshake</h2>
        <p className="text-sm text-text-muted leading-relaxed uppercase font-bold text-[10px] tracking-widest">
          AlphaForge requires a unique node identifier for session persistence and institutional cluster reporting.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="node-id" className="text-[10px] font-black uppercase text-text-muted tracking-widest">Institutional Node ID</Label>
        <Input 
          id="node-id"
          value={name} 
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Enter your terminal name..."
          className="h-14 bg-elevated/50 border-border-subtle focus:ring-primary/20 font-bold uppercase text-xs"
          autoFocus
        />
      </div>

      <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 flex gap-3 items-start">
        <div className="w-1 h-1 rounded-full bg-primary mt-1.5 shrink-0" />
        <p className="text-[10px] font-bold text-text-secondary uppercase leading-relaxed">
          Your node identifier will be used to anchor all algorithmic resolutions to your private audit trail.
        </p>
      </div>
    </div>
  );
}
