'use client';

import { ChatAction } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Zap, Eye, Copy, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { useToast } from '@/hooks/use-toast';

interface MessageActionsProps {
  actions?: ChatAction[];
  isLoading?: boolean;
}

/**
 * MessageActions - Renders action buttons from AI response.
 * Handles copy strategy, view backtest, view signal, and navigation.
 */
export function MessageActions({ actions, isLoading }: MessageActionsProps) {
  const { toast } = useToast();

  if (!actions || actions.length === 0 || isLoading) {
    return null;
  }

  const handleCopy = async (action: ChatAction) => {
    if (!action.targetId) return;

    try {
      // In production, copy actual strategy code or JSON to clipboard
      await navigator.clipboard.writeText(`Strategy ID: ${action.targetId}`);
      toast({
        title: 'Copied',
        description: `${action.label} copied to clipboard`,
      });
    } catch (e) {
      toast({
        title: 'Failed',
        description: 'Could not copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  const handleAction = (action: ChatAction) => {
    switch (action.type) {
      case 'copy_strategy':
        handleCopy(action);
        break;
      case 'view_backtest':
      case 'view_signal':
        if (action.url) window.open(action.url, '_blank');
        break;
      case 'trade':
        if (action.url) window.open(action.url, '_blank');
        break;
      case 'link':
        if (action.url) window.location.href = action.url;
        break;
    }
  };

  const renderIcon = (type: ChatAction['type']) => {
    switch (type) {
      case 'copy_strategy':
        return <Copy size={12} />;
      case 'view_backtest':
        return <Eye size={12} />;
      case 'view_signal':
        return <Zap size={12} />;
      case 'trade':
        return <ArrowRight size={12} />;
      case 'link':
        return <ArrowRight size={12} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {actions.map((action, i) => {
        // Render as Link for navigation actions
        if (action.type === 'link' && action.url) {
          return (
            <Link key={i} href={action.url}>
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-[9px] font-black uppercase px-3 gap-1 border-border-subtle bg-elevated/50 hover:bg-elevated text-text-secondary hover:text-text-primary transition-all rounded-lg"
              >
                {renderIcon(action.type)}
                <span>{action.label}</span>
              </Button>
            </Link>
          );
        }

        // Render as button for other actions
        return (
          <Button
            key={i}
            variant="outline"
            size="sm"
            onClick={() => handleAction(action)}
            className="h-8 text-[9px] font-black uppercase px-3 gap-1 border-border-subtle bg-elevated/50 hover:bg-elevated text-text-secondary hover:text-text-primary transition-all rounded-lg"
          >
            {renderIcon(action.type)}
            <span>{action.label}</span>
          </Button>
        );
      })}
    </div>
  );
}
