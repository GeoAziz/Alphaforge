import { MarketDataQuality } from '@/lib/types';

export const mockMarketDataQualities: MarketDataQuality[] = [
  { asset: 'BTCUSDT', source: 'Binance Cluster', freshness: 12, status: 'Optimal' },
  { asset: 'ETHUSDT', source: 'Coinbase Institutional', freshness: 45, status: 'Optimal' },
  { asset: 'SOLUSDT', source: 'Kraken Feed', freshness: 150, status: 'Degraded' }
];
