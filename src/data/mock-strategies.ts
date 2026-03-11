import { Strategy, MarketplaceStrategy } from '@/lib/types';

export const mockUserStrategies: Strategy[] = [
  {
    id: 'strat-1',
    name: 'Momentum Breakout Core',
    description: 'High-frequency algorithmic pursuit of volatility clusters.',
    winRate: 68.4,
    avgRoi: 12.4,
    maxDrawdown: 8.5,
    sharpeRatio: 1.92,
    totalTrades: 1240,
    profitFactor: 2.15,
    riskLevel: 'Medium',
    isActive: true
  },
  {
    id: 'strat-2',
    name: 'Liquid Alpha Neutral',
    description: 'Delta-neutral market making focused on funding rate capture.',
    winRate: 84.2,
    avgRoi: 4.5,
    maxDrawdown: 2.1,
    sharpeRatio: 3.42,
    totalTrades: 8500,
    profitFactor: 3.84,
    riskLevel: 'Low',
    isActive: true
  }
];

export const mockMarketplaceStrategies: MarketplaceStrategy[] = [
  {
    id: 'ms-1',
    name: 'Black Swan Defender',
    creator: 'Cipher Capital',
    description: 'Tail-risk protection strategy optimized for extreme volatility events.',
    winRate: 92.1,
    roi: 45.2,
    maxDrawdown: 4.2,
    subscribers: 1240,
    riskLevel: 'Low',
    monthlyPrice: 299,
    isVerified: true
  },
  {
    id: 'ms-2',
    name: 'Neural Momentum V4',
    creator: 'AlphaForge Labs',
    description: 'Advanced machine learning engine synthesizing cross-exchange sentiment.',
    winRate: 64.8,
    roi: 124.5,
    maxDrawdown: 18.4,
    subscribers: 850,
    riskLevel: 'High',
    monthlyPrice: 499,
    isVerified: true
  }
];