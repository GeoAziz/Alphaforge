'use client';

import { useEffect, useRef } from 'react';
import { X, Trash2, ShieldAlert, Cpu } from 'lucide-react';
import { MessageBubble } from './message-bubble';
import { ChatInput } from './chat-input';
import { ChatLoader } from './chat-loader';
import { useChatMessages } from '@/hooks/use-chat-messages';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const { messages, isLoading, addMessage, streamResponse, clearChat } = useChatMessages();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (text: string) => {
    addMessage('user', text);
    await streamResponse(text);
  };

  return (
    <div className={cn(
      "fixed inset-y-0 right-0 z-[100] w-full sm:w-[400px] glass border-l border-border-subtle flex flex-col transition-transform duration-500 ease-out-custom shadow-2xl",
      isOpen ? "translate-x-0" : "translate-x-full"
    )}>
      {/* Header */}
      <div className="p-6 border-b border-border-subtle bg-elevated/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shadow-inner">
            <Cpu size={20} className="animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-black uppercase tracking-tighter leading-none">AlphaAI Intelligence</h2>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
              <span className="text-[9px] font-black text-green uppercase tracking-widest">Core Sync Active</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={clearChat} className="w-8 h-8 text-text-muted hover:text-red rounded-lg" title="Purge History">
            <Trash2 size={16} />
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose} className="w-8 h-8 text-text-muted hover:text-text-primary rounded-lg">
            <X size={20} />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 scrollbar-hide space-y-2"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-40 py-20">
            <div className="w-16 h-16 rounded-3xl bg-elevated flex items-center justify-center text-text-muted border border-border-subtle">
              <ShieldAlert size={32} />
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-black uppercase tracking-widest text-text-primary">Intelligence Node Idle</h3>
              <p className="text-[10px] font-bold text-text-muted uppercase max-w-[200px] leading-relaxed">
                Query AlphaAI for signal rationale, risk assessments, or strategy telemetry.
              </p>
            </div>
          </div>
        ) : (
          messages.map(msg => <MessageBubble key={msg.id} message={msg} />)
        )}
        {isLoading && <ChatLoader />}
      </div>

      {/* Input Area */}
      <ChatInput onSend={handleSend} disabled={isLoading} />

      {/* Token Usage Indicator */}
      <div className="px-6 py-3 border-t border-border-subtle bg-elevated/10 flex items-center justify-between">
        <span className="text-[8px] font-black text-text-muted uppercase tracking-widest">Compute Quota</span>
        <div className="flex items-center gap-2">
          <div className="h-1 w-20 bg-border-subtle rounded-full overflow-hidden">
            <div className="h-full bg-primary w-[12%]" />
          </div>
          <span className="text-[8px] font-black text-primary uppercase">12 / 5,000 Nodes</span>
        </div>
      </div>
    </div>
  );
}
