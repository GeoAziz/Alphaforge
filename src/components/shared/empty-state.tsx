'use client';

import { ReactNode } from 'react';
import { LucideIcon, ShieldAlert } from 'lucide-react';
import { SpotlightCard } from './spotlight-card';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

/**
 * Standardized EmptyState for AlphaForge terminal nodes.
 * Used for "No Data", "Auth Required", or "Restricted" views.
 */
export function EmptyState({
  title,
  description,
  icon: Icon = ShieldAlert,
  actionLabel,
  onAction,
  className
}: EmptyStateProps) {
  return (
    <div className="h-full flex items-center justify-center p-8 min-h-[400px]">
      <SpotlightCard className={className || "max-w-md p-10 text-center space-y-6"}>
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
          <Icon size={32} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-black uppercase tracking-tighter text-text-primary">{title}</h2>
          <p className="text-sm text-text-muted leading-relaxed">{description}</p>
        </div>
        {actionLabel && (
          <Button 
            onClick={onAction}
            className="w-full h-12 bg-primary text-primary-foreground font-black uppercase text-xs tracking-widest rounded-lg hover:opacity-90 transition-opacity"
          >
            {actionLabel}
          </Button>
        )}
      </SpotlightCard>
    </div>
  );
}
