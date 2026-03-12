'use client';

import { Zap, ShieldAlert, CheckCircle2, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Toast, ToastClose, ToastDescription, ToastTitle } from '@/components/ui/toast';

interface NotificationToastProps {
  type: 'signal' | 'trade' | 'risk' | 'system';
  title: string;
  message: string;
}

/**
 * NotificationToast - Technical glass treatment for terminal alerts.
 */
export function NotificationToast({ type, title, message }: NotificationToastProps) {
  const icons = {
    signal: <Zap size={16} className="text-primary" />,
    trade: <CheckCircle2 size={16} className="text-green" />,
    risk: <ShieldAlert size={16} className="text-red" />,
    system: <Info size={16} className="text-accent" />,
  };

  const borders = {
    signal: 'border-l-primary',
    trade: 'border-l-green',
    risk: 'border-l-red',
    system: 'border-l-accent',
  };

  return (
    <div className={cn(
      "glass border-l-4 p-4 pr-10 shadow-2xl flex gap-4 min-w-[320px] max-w-md animate-in slide-in-from-top-4 sm:slide-in-from-right-4 duration-350 ease-spring",
      borders[type]
    )}>
      <div className={cn(
        "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
        type === 'signal' ? "bg-primary/10" : type === 'trade' ? "bg-green/10" : type === 'risk' ? "bg-red/10" : "bg-accent/10"
      )}>
        {icons[type]}
      </div>
      <div className="space-y-1 overflow-hidden">
        <div className="text-[11px] font-black uppercase text-text-primary tracking-tight leading-tight">
          {title}
        </div>
        <div className="text-[10px] font-medium text-text-muted uppercase leading-relaxed line-clamp-2">
          {message}
        </div>
      </div>
    </div>
  );
}
