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
    description: 'Tail-risk protection strategy optimized for extreme volatility events using deep-out-of-the-money puts and cross-exchange volatility clusters.',
    winRate: 92.1,
    roi: 45.2,
    maxDrawdown: 4.2,
    subscribers: 1240,
    riskLevel: 'Low',
    monthlyPrice: 299,
    isVerified: true,
    reputationScore: 4.9,
    verificationStage: 5,
    sharpeRatio: 4.82,
    performanceBadge: 'Best in Category',
    paperTradeDelta: +0.42,
    pricingModel: 'Subscription'
  },
  {
    id: 'ms-2',
    name: 'Neural Momentum V4',
    creator: 'AlphaForge Labs',
    description: 'Advanced machine learning engine synthesizing cross-exchange sentiment and institutional order flow using a proprietary LSTM-Transformer model.',
    winRate: 64.8,
    roi: 124.5,
    maxDrawdown: 18.4,
    subscribers: 850,
    riskLevel: 'High',
    monthlyPrice: 499,
    isVerified: true,
    reputationScore: 4.7,
    verificationStage: 5,
    sharpeRatio: 3.24,
    performanceBadge: 'Trending',
    paperTradeDelta: -1.2,
    pricingModel: 'Profit Share'
  },
  {
    id: 'ms-3',
    name: 'Liquid Alpha Scalper',
    creator: 'Vertex Node',
    description: 'Ultra-low latency scalping engine targeting sub-second price inefficiencies in high-volume perp markets.',
    winRate: 72.4,
    roi: 18.5,
    maxDrawdown: 6.8,
    subscribers: 3200,
    riskLevel: 'Medium',
    monthlyPrice: 150,
    isVerified: true,
    reputationScore: 4.5,
    verificationStage: 4,
    sharpeRatio: 2.95,
    performanceBadge: 'Trending',
    paperTradeDelta: +0.15,
    pricingModel: 'Subscription'
  },
  {
    id: 'ms-4',
    name: 'Funding Arbitrage',
    creator: 'Basis Core',
    description: 'Delta-neutral strategy capturing funding rate spreads across Binance and Bybit futures markets.',
    winRate: 98.2,
    roi: 12.1,
    maxDrawdown: 1.5,
    subscribers: 540,
    riskLevel: 'Low',
    monthlyPrice: 99,
    isVerified: false,
    reputationScore: 3.8,
    verificationStage: 2,
    sharpeRatio: 4.12,
    performanceBadge: 'New',
    paperTradeDelta: -0.05,
    pricingModel: 'Profit Share'
  }
];
