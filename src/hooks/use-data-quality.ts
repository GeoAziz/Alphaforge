
'use client';

import { useState, useEffect } from 'react';
import { MarketDataQuality } from '@/lib/types';
import { api } from '@/lib/api';

/**
 * useDataQuality - Periodically checks the health of institutional data feeds.
 */
export function useDataQuality() {
  const [quality, setQuality] = useState<MarketDataQuality[]>([]);
  const [isSyncing, setIsSyncing] = useState(true);

  useEffect(() => {
    const fetchQuality = async () => {
      try {
        const data = await api.market.getDataQuality();
        setQuality(data);
      } catch (e) {
        console.error('Data quality sync failed');
      } finally {
        setIsSyncing(false);
      }
    };

    fetchQuality();
    const interval = setInterval(fetchQuality, 30000); // 30s institutional poll

    return () => clearInterval(interval);
  }, []);

  return { quality, isSyncing };
}
