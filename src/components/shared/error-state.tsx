'use client';

import { LucideIcon, RefreshCw, WifiOff } from 'lucide-react';
import { SpotlightCard } from './spotlight-card';
import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  icon?: LucideIcon;
  onRetry?: () => void;
}

/**
 * ErrorState component for handling node connectivity or permission failures.
 */
export function ErrorState({
  title = "Node Connectivity Failure",
  message = "Institutional data stream interrupted. Re-synchronizing frequency...",
  icon: Icon = WifiOff,
  onRetry
}: ErrorStateProps) {
  return (
    <div className="h-full flex items-center justify-center p-8">
      <SpotlightCard className="max-w-md p-10 text-center space-y-6 border-red/20 bg-red/5">
        <div className="w-16 h-16 rounded-full bg-red/10 flex items-center justify-center mx-auto text-red">
          <Icon size={32} />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-black uppercase tracking-tighter text-red">{title}</h2>
          <p className="text-sm text-text-muted leading-relaxed font-medium">{message}</p>
        </div>
        {onRetry && (
          <Button 
            onClick={onRetry}
            variant="outline"
            className="w-full border-red/30 text-red hover:bg-red/5 font-black uppercase text-xs h-12 gap-2"
          >
            <RefreshCw size={14} /> Re-Initialize Session
          </Button>
        )}
      </SpotlightCard>
    </div>
  );
}
