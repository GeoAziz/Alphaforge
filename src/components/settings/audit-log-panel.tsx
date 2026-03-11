'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Badge } from '@/components/ui/badge';
import { Clock } from 'lucide-react';

const auditLog = [
  { action: 'Position Opened', details: 'BTC LONG @ 42,500', timestamp: '2h ago', status: 'success' },
  { action: 'API Key Connected', details: 'Binance trading account', timestamp: '1d ago', status: 'success' },
  { action: 'Risk Settings Updated', details: 'Position size limit: 2.5%', timestamp: '3d ago', status: 'success' },
  { action: 'Position Closed', details: 'ETH SHORT - +2.4% PnL', timestamp: '5d ago', status: 'success' },
  { action: 'Margin Called', details: 'Risk threshold exceeded', timestamp: '7d ago', status: 'warning' },
];

export function AuditLogPanel() {
  return (
    <SpotlightCard className="p-8">
      <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary mb-6">
        <Clock size={18} className="text-accent" />
        Audit Trail
      </h3>

      <div className="space-y-3">
        {auditLog.map((entry, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle hover:bg-elevated/40 transition-all">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="font-bold text-text-primary text-sm">{entry.action}</div>
                <Badge className={entry.status === 'success' ? "bg-green/10 text-green border-green/20 text-[10px]" : "bg-amber/10 text-amber border-amber/20 text-[10px]"}>
                  {entry.status === 'success' ? '✓ Success' : '⚠ Warning'}
                </Badge>
              </div>
              <span className="text-[10px] text-text-muted">{entry.timestamp}</span>
            </div>
            <div className="text-[11px] text-text-secondary">{entry.details}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-border-subtle">
        <button className="text-xs font-black text-primary hover:underline uppercase">View Full History →</button>
      </div>
    </SpotlightCard>
  );
}
