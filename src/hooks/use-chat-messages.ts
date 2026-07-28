'use client';

import { useState, useCallback, useEffect } from 'react';
import { ChatMessage, ChatAction } from '@/lib/types';
import { api } from '@/lib/api';
import { useUser } from '@/firebase';

/**
 * useChatMessages - Manages AlphaAI chat state, backed by the real
 * /api/chat/* endpoints (backend/services/chat_service.py). History is
 * loaded from the server per-user; nothing is generated client-side.
 */
export function useChatMessages() {
  const { user } = useUser();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Load real history from the backend once we know who the user is.
  useEffect(() => {
    if (!user?.uid || historyLoaded) return;
    api.chat.getHistory(user.uid)
      .then(setMessages)
      .catch((e) => console.error('Failed to load chat history:', e))
      .finally(() => setHistoryLoaded(true));
  }, [user?.uid, historyLoaded]);

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
    if (!user?.uid) {
      addMessage('assistant', 'You need to be signed in to chat with AlphaAI.');
      return;
    }

    setIsLoading(true);
    try {
      const result = await api.chat.sendMessage({ user_id: user.uid, message: question });
      const responseText = result.ai_response || "Sorry, I couldn't generate a response.";

      // Character-reveal the real response for the existing terminal-typing feel.
      const assistantMsg = addMessage('assistant', '');
      let currentText = '';
      for (let i = 0; i < responseText.length; i++) {
        currentText += responseText[i];
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last && last.id === assistantMsg.id) {
            return [...prev.slice(0, -1), { ...last, content: currentText }];
          }
          return prev;
        });
        await new Promise(resolve => setTimeout(resolve, 8));
      }
    } catch (e) {
      console.error('Chat message failed:', e);
      addMessage('assistant', 'AlphaAI is temporarily unavailable. Please try again shortly.');
    } finally {
      setIsLoading(false);
    }
  }, [user?.uid, addMessage]);

  const clearChat = useCallback(() => {
    // Clears the local view only — server-side history is the source of
    // truth and is intentionally not deleted from here (audit trail).
    setMessages([]);
  }, []);

  return { messages, isLoading, addMessage, streamResponse, clearChat };
}
