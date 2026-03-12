'use client';

import { useState, useCallback, useEffect } from 'react';
import { ChatMessage, ChatAction } from '@/lib/types';

/**
 * useChatMessages - Manages institutional AI chat state and simulated streaming.
 */
export function useChatMessages() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('af_chat_history');
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse chat history');
      }
    }
  }, []);

  // Save history on change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('af_chat_history', JSON.stringify(messages.slice(-50)));
    }
  }, [messages]);

  const addMessage = useCallback((role: 'user' | 'assistant', content: string, actions?: ChatAction[]) => {
    const newMessage: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      role,
      content,
      timestamp: new Date().toISOString(),
      actions,
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  }, []);

  const streamResponse = useCallback(async (question: string) => {
    setIsLoading(true);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    // Simple response logic for Phase 1 Mock
    let responseText = "";
    let actions: ChatAction[] = [];

    if (question.toLowerCase().includes('signal')) {
      responseText = "Analyzing recent signals... I've detected a high-confidence Momentum Breakout on BTCUSDT. The pattern has a 72% historical win rate. Would you like to view the full rational?";
      actions = [{ label: 'View Signal', type: 'view_signal', targetId: 'sig-1' }];
    } else if (question.toLowerCase().includes('risk') || question.toLowerCase().includes('exposure')) {
      responseText = "Your current portfolio risk score is 6.8 (Medium-High). You have 3 open positions with a combined margin utilization of 28%. I recommend reviewing your stop-loss levels for SOLUSDT.";
      actions = [{ label: 'Risk Settings', type: 'link', url: '/settings' }];
    } else {
      responseText = "I am AlphaAI, your institutional trading assistant. I can analyze signals, check portfolio risk, or explain strategy logic. How can I assist your terminal session today?";
    }

    // "Streaming" the response
    const assistantMsg = addMessage('assistant', "", actions);
    let currentText = "";
    
    for (let i = 0; i < responseText.length; i++) {
      currentText += responseText[i];
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.id === assistantMsg.id) {
          return [...prev.slice(0, -1), { ...last, content: currentText }];
        }
        return prev;
      });
      await new Promise(resolve => setTimeout(resolve, 15)); // character streaming speed
    }

    setIsLoading(false);
  }, [addMessage]);

  const clearChat = useCallback(() => {
    setMessages([]);
    localStorage.removeItem('af_chat_history');
  }, []);

  return { messages, isLoading, addMessage, streamResponse, clearChat };
}
