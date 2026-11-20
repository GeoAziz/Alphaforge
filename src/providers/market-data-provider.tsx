'use client';

import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { api } from '@/lib/api';
import { MarketTicker } from '@/lib/types';
import { useWebSocket } from '@/hooks/use-websocket';

interface MarketDataContextType {
  tickers: MarketTicker[];
  isConnected: boolean;
  isStale: boolean;
  lastUpdated: Date | null;
  error: Error | null;
  refresh: () => Promise<void>;
}

const MarketDataContext = createContext<MarketDataContextType | null>(null);

const MAX_CACHE_AGE_MS = 15000;

export function MarketDataProvider({ children }: { children: React.ReactNode }) {
  const [tickers, setTickers] = useState<MarketTicker[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isStale, setIsStale] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  // Single authoritative WebSocket listener for public market updates
  const { data: wsData, isConnected, error: wsError } = useWebSocket<any>('/ws/market-updates');

  // Initial REST fetch and fallback polling
  const fetchTickers = async () => {
    try {
      const data = await api.market.getTickers();
      if (Array.isArray(data) && data.length > 0) {
        setTickers(data);
        setLastUpdated(new Date());
        setIsStale(false);
      }
    } catch (err: any) {
      setError(err);
    }
  };

  useEffect(() => {
    fetchTickers();
    // Fallback polling every 10 seconds if WS is disconnected
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchTickers();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [isConnected]);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (wsData) {
      if (Array.isArray(wsData)) {
        setTickers(wsData);
      } else if (wsData.ticker) {
        setTickers((prev) => {
          const incomingAsset = wsData.ticker.asset || wsData.ticker.symbol;
          const index = prev.findIndex((t) => t.asset === incomingAsset || (t as any).symbol === incomingAsset);
          if (index >= 0) {
            const next = [...prev];
            next[index] = { ...next[index], ...wsData.ticker };
            return next;
          }
          return [wsData.ticker, ...prev];
        });
      }
      setLastUpdated(new Date());
      setIsStale(false);
    }
  }, [wsData]);

  // Check data staleness every 5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      if (lastUpdated) {
        const age = Date.now() - lastUpdated.getTime();
        setIsStale(age > MAX_CACHE_AGE_MS);
      }
    }, 5000);
    return () => clearInterval(timer);
  }, [lastUpdated]);

  const value = useMemo(
    () => ({
      tickers,
      isConnected,
      isStale,
      lastUpdated,
      error: error || wsError,
      refresh: fetchTickers,
    }),
    [tickers, isConnected, isStale, lastUpdated, error, wsError]
  );

  return <MarketDataContext.Provider value={value}>{children}</MarketDataContext.Provider>;
}

export function useMarketData() {
  const context = useContext(MarketDataContext);
  if (!context) {
    throw new Error('useMarketData must be used within a MarketDataProvider');
  }
  return context;
}
