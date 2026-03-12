'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Cpu, Command } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-border-subtle bg-surface/50 backdrop-blur-md">
      <div className="relative group">
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask AlphaAI... (⌘↵ to Engage)"
          className="min-h-[80px] max-h-[160px] bg-elevated/30 border-border-subtle focus:border-primary/50 text-[11px] font-medium uppercase scrollbar-hide pr-12 rounded-xl resize-none"
          disabled={disabled}
        />
        <Button 
          size="icon"
          onClick={handleSubmit}
          disabled={!text.trim() || disabled}
          className="absolute right-3 bottom-3 w-8 h-8 bg-primary text-primary-foreground rounded-lg shadow-lg hover:scale-105 transition-transform"
        >
          <Send size={14} />
        </Button>
      </div>
      <div className="mt-3 flex items-center justify-between px-1">
        <div className="flex items-center gap-2 text-[8px] font-black text-text-muted uppercase tracking-widest">
          <Cpu size={10} className="text-primary" />
          Neural Engine V4.2
        </div>
        <div className="text-[8px] font-black text-text-muted uppercase flex items-center gap-1">
          <Command size={8} /> ↵ Engage Node
        </div>
      </div>
    </div>
  );
}
