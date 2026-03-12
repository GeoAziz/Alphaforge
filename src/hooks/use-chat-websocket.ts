'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { ChatMessage } from '@/lib/types';

export interface UseChatWebSocketOptions {
  url?: string;
  onMessage?: (message: ChatMessage) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

/**
 * useChatWebSocket - Manages WebSocket connection for real-time chat.
 * For Phase 1, uses simulated connection. Backend integration ready.
 */
export function useChatWebSocket(options: UseChatWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // 1 second

  const {
    url = typeof window !== 'undefined' && window.location.protocol === 'https:'
      ? `wss://${window.location.host}/api/chat/ws`
      : `ws://${window.location.host}/api/chat/ws`,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
  } = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setIsConnecting(true);

    try {
      // Phase 1: Simulated WebSocket for demo purposes
      // Backend: Replace with real WebSocket initialization when API is ready
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      wsRef.current.onmessage = (event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data) as ChatMessage;
          onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current.onerror = (event: Event) => {
        const wsError = new Error('WebSocket connection error');
        setError(wsError);
        onError?.(wsError);
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        // Exponential backoff reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };
    } catch (e) {
      const connectError = e instanceof Error ? e : new Error('Failed to establish WebSocket connection');
      setError(connectError);
      setIsConnecting(false);
      onError?.(connectError);
    }
  }, [url, onMessage, onError, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const send = useCallback((message: ChatMessage | Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    wsRef.current.send(JSON.stringify(message));
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    // Phase 1: Skip auto-connect for simulated mode
    // In production, uncomment the line below
    // connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    send,
  };
}
