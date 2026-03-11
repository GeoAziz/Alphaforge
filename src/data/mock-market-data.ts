import { MarketTicker, MarketSentiment, FundingRate, OpenInterest, OnChainActivity, LiquidationCluster } from '@/lib/types';

export const mockTickers: MarketTicker[] = [
  { id: 'btc-usdt', asset: 'BTCUSDT', price: 68420.50, change24h: 2.45, change24hAbs: 1640.20, volume24h: 1240000000, high24h: 69200, low24h: 66800 },
  { id: 'eth-usdt', asset: 'ETHUSDT', price: 3450.25, change24h: -1.20, change24hAbs: -42.10, volume24h: 850000000, high24h: 3550, low24h: 3380 },
  { id: 'sol-usdt', asset: 'SOLUSDT', price: 142.30, change24h: 5.60, change24hAbs: 7.55, volume24h: 420000000, high24h: 148, low24h: 132 },
  { id: 'link-usdt', asset: 'LINKUSDT', price: 18.45, change24h: 1.15, change24hAbs: 0.21, volume24h: 120000000, high24h: 19.20, low24h: 17.80 },
  { id: 'arb-usdt', asset: 'ARBUSDT', price: 1.85, change24h: -3.40, change24hAbs: -0.06, volume24h: 95000000, high24h: 1.95, low24h: 1.80 },
  { id: 'pepe-usdt', asset: 'PEPEUSDT', price: 0.00000842, change24h: 12.40, change24hAbs: 0.00000092, volume24h: 350000000, high24h: 0.000009, low24h: 0.000007 }
];

export const mockSentiment: MarketSentiment = {
  id: 'latest',
  score: 72,
  label: 'Greed',
  factors: {
    social: 84,
    volatility: 42,
    orderBook: 68
  }
};

export const mockFundingRates: FundingRate[] = [
  { id: 'f-1', asset: 'BTCUSDT', exchange: 'Binance', rate: 0.0001, nextFundingTime: new Date().toISOString() },
  { id: 'f-2', asset: 'ETHUSDT', exchange: 'Bybit', rate: 0.00015, nextFundingTime: new Date().toISOString() },
  { id: 'f-3', asset: 'SOLUSDT', exchange: 'OKX', rate: -0.00005, nextFundingTime: new Date().toISOString() }
];

export const mockOpenInterest: OpenInterest[] = [
  { id: 'oi-1', asset: 'BTCUSDT', value: 12400000000, change24h: 4.2 },
  { id: 'oi-2', asset: 'ETHUSDT', value: 8500000000, change24h: -1.5 }
];

export const mockOnChainActivity: OnChainActivity[] = [
  { id: 'oa-1', type: 'whale_move', asset: 'BTC', amount: 450, valueUsd: 30789000, from: 'Unknown Wallet', to: 'Coinbase Institutional', timestamp: new Date().toISOString() },
  { id: 'oa-2', type: 'exchange_flow', asset: 'ETH', amount: 12000, valueUsd: 41400000, from: 'Binance', to: 'Private Storage', timestamp: new Date().toISOString() },
  { id: 'oa-3', type: 'contract_deploy', asset: 'SOL', amount: 0, valueUsd: 0, from: 'Developer Engine', to: 'Mainnet-Beta', timestamp: new Date().toISOString() }
];

export const mockLiquidationClusters: LiquidationCluster[] = [
  { asset: 'BTC', value: 45, type: 'long' },
  { asset: 'ETH', value: 25, type: 'short' },
  { asset: 'SOL', value: 15, type: 'long' },
  { asset: 'LINK', value: 10, type: 'short' },
  { asset: 'ARB', value: 5, type: 'long' }
];