'use client';

import { ChatMessage } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Bot, User, Cpu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MessageActions } from './message-actions';
import Link from 'next/link';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAI = message.role === 'assistant';

  return (
    <div className={cn(
      "flex w-full gap-3 mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300",
      isAI ? "justify-start" : "justify-end"
    )}>
      {isAI && (
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shrink-0">
          <Bot size={16} />
        </div>
      )}
      
      <div className={cn(
        "max-w-[85%] space-y-3",
        isAI ? "items-start" : "items-end flex flex-col"
      )}>
        <div className={cn(
          "p-4 rounded-2xl text-xs font-medium leading-relaxed uppercase",
          isAI 
            ? "bg-elevated/50 border border-border-subtle text-text-secondary rounded-tl-none" 
            : "bg-primary text-primary-foreground rounded-tr-none shadow-lg"
        )}>
          {message.content || (isAI && <div className="flex gap-1"><div className="w-1 h-1 bg-text-muted rounded-full animate-pulse" /><div className="w-1 h-1 bg-text-muted rounded-full animate-pulse delay-75" /><div className="w-1 h-1 bg-text-muted rounded-full animate-pulse delay-150" /></div>)}
        </div>

        {isAI && message.actions && message.actions.length > 0 && (
          <MessageActions actions={message.actions} />
        )}

        <div className="text-[8px] font-black text-text-muted uppercase tracking-widest px-1">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          {isAI && " • AlphaAI Node"}
        </div>
      </div>

      {!isAI && (
        <div className="w-8 h-8 rounded-lg bg-elevated flex items-center justify-center text-text-muted border border-border-subtle shrink-0">
          <User size={16} />
        </div>
      )}
    </div>
  );
}
