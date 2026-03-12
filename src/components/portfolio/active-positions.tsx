'use client';

import { Position } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { 
  Table, 
  TableBody, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { PositionRow } from './position-row';
import { Briefcase, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ActivePositionsProps {
  positions: Position[] | null;
  isLoading: boolean;
}

/**
 * ActivePositions - Grid of active terminal positions with real-time jitter.
 */
export function ActivePositions({ positions, isLoading }: ActivePositionsProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h3 className="text-sm font-black uppercase text-text-muted flex items-center gap-2 tracking-widest">
          <Briefcase size={16} className="text-primary" />
          Active Risk Exposure
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
          <span className="text-[9px] font-black text-green uppercase tracking-widest">Live Sync</span>
        </div>
      </div>

      <SpotlightCard className="p-0 overflow-hidden border-border-subtle bg-surface/30 backdrop-blur-md">
        <Table>
          <TableHeader className="bg-elevated/50">
            <TableRow className="border-border-subtle hover:bg-transparent">
              <TableHead className="text-[10px] font-black uppercase tracking-widest">Node Cluster</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest">Entry</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest">Live Tick</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest text-right">PnL Delta</TableHead>
              <TableHead className="text-[10px] font-black uppercase tracking-widest text-right hidden md:table-cell">Risk</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array(3).fill(0).map((_, i) => (
                <TableRow key={i} className="border-border-subtle">
                  <TableHead colSpan={5} className="h-16 animate-pulse bg-elevated/10" />
                </TableRow>
              ))
            ) : !positions || positions.length === 0 ? (
              <TableRow>
                <TableHead colSpan={5} className="h-32 text-center text-[10px] font-black uppercase text-text-muted opacity-50 italic">
                  Scanning for active node positions...
                </TableHead>
              </TableRow>
            ) : (
              positions.map((pos) => (
                <PositionRow key={pos.id} position={pos} />
              ))
            )}
          </TableBody>
        </Table>
      </SpotlightCard>
    </div>
  );
}
