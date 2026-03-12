
'use client';

import { Badge } from "@/components/ui/badge";
import { Microscope } from "lucide-react";

interface PaperTradeBadgeProps {
  status?: string;
}

/**
 * PaperTradeBadge - Shows gate results for marketplace subscriptions.
 */
export function PaperTradeBadge({ status = "Simulating" }: PaperTradeBadgeProps) {
  return (
    <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 gap-1.5 py-1 px-3 uppercase font-black text-[9px] tracking-widest">
      <Microscope size={12} />
      Handshake: {status}
    </Badge>
  );
}
