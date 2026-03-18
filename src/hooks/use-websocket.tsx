'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useUser } from '@/firebase';
import { useRouter } from 'next/navigation';

interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
}

interface UseWebSocketOptions {
  reconnect?: boolean;
  maxReconnect?: number;
  reconnectDelay?: number;
}

/**
 * Hook for connecting to backend WebSocket endpoints.
 * 
 * Usage:
 *   const { data, isConnected, error, send } = useWebSocket<MarketUpdate>('/ws/market-updates');
 *   
 *   useEffect(() => {
 *     if (data) {
 *       console.log('Market data:', data);
 *     }
 *   }, [data]);
 */
export function useWebSocket<T = any>(
  path: string,
  options: UseWebSocketOptions = {},
) {
  const { reconnect = true, maxReconnect = 10, reconnectDelay = 1000 } = options;

  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isAttemptingReconnect, setIsAttemptingReconnect] = useState(false);

  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimer = useRef<NodeJS.Timeout | null>(null);

  const { user } = useUser();
  const router = useRouter();

  const connect = useCallback(() => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      // Convert http/https to ws/wss
      const wsUrl = `${API_URL.replace(/^http/, 'ws')}${path}`;

      console.log(`[WebSocket] Connecting to ${wsUrl}`);
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log(`[WebSocket] Connected to ${path}`);
        setIsConnected(true);
        setError(null);
        reconnectCount.current = 0;
        setIsAttemptingReconnect(false);

        // Send initial authentication if user exists
        if (user?.uid && ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(
            JSON.stringify({
              type: 'auth',
              user_id: user.uid,
            })
          );
        }

        // Start heartbeat - send every 20 seconds to prevent ngrok timeout
        heartbeatTimer.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 20000); // Every 20 seconds instead of 30
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage<T>;
          
          if (message.type === 'pong') {
            // Heartbeat response, ignore
            return;
          }

          setData(message.data);
        } catch (e) {
          console.error('[WebSocket] Failed to parse message:', e);
        }
      };

      ws.current.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        const err = new Error('WebSocket error');
        setError(err);
      };

      ws.current.onclose = (event) => {
        console.log(
          `[WebSocket] Disconnected ${event.code} (${event.reason || 'no reason'})`
        );
        setIsConnected(false);

        if (heartbeatTimer.current) {
          clearInterval(heartbeatTimer.current);
        }

        // Attempt reconnection with exponential backoff
        if (reconnect && reconnectCount.current < maxReconnect) {
          reconnectCount.current += 1;
          setIsAttemptingReconnect(true);
          
          // Exponential backoff: 1s, 2s, 4s, 8s, 16s, etc.
          const delay = Math.min(reconnectDelay * Math.pow(2, reconnectCount.current - 1), 30000);
          console.log(
            `[WebSocket] Reconnecting in ${delay}ms... (${reconnectCount.current}/${maxReconnect})`
          );

          reconnectTimer.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectCount.current >= maxReconnect) {
          console.error('[WebSocket] Max reconnect attempts reached, giving up');
          setError(new Error('Max reconnection attempts reached'));
        }
      };
    } catch (e) {
      console.error('[WebSocket] Connection error:', e);
      setError(e instanceof Error ? e : new Error(String(e)));
    }
  }, [path, reconnect, maxReconnect, reconnectDelay, user?.uid]);

  const send = useCallback((message: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (e) {
        console.error('[WebSocket] Send error:', e);
      }
    } else {
      console.warn('[WebSocket] Cannot send: connection not open');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
    }
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.close();
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    data,
    isConnected,
    isAttemptingReconnect,
    error,
    send,
    disconnect,
    reconnectCount: reconnectCount.current,
  };
}

/**
 * Component to display WebSocket connection status.
 */
export function WebSocketStatus({ className = '' }: { className?: string }) {
  const { isConnected, isAttemptingReconnect } = useWebSocket('/ws/market-updates');

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`w-2 h-2 rounded-full transition-colors ${
          isConnected
            ? 'bg-green-500'
            : isAttemptingReconnect
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-red-500'
        }`}
      />
      <span className="text-xs font-medium text-gray-600">
        {isConnected ? 'Live' : isAttemptingReconnect ? 'Reconnecting...' : 'Offline'}
      </span>
    </div>
  );
}
