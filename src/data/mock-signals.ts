import { Signal } from '@/lib/types';
import { subHours, subDays } from 'date-fns';

export const mockSignals: Signal[] = [
  {
    id: 'sig-1',
    asset: 'BTCUSDT',
    direction: 'LONG',
    entryPrice: 68420.50,
    stopLoss: 66900.00,
    takeProfit: 71200.00,
    confidence: 92,
    strategy: 'Momentum Breakout',
    strategyId: 'strat-1',
    status: 'active',
    riskRewardRatio: 1.83,
    createdAt: subHours(new Date(), 2).toISOString(),
    closedAt: null,
    pnlPercent: null,
    drivers: [
      { label: 'Bullish engulfing on 4H', weight: 0.8, active: true },
      { label: 'RSI divergence', weight: 0.6, active: true },
      { label: 'Increased volume profile', weight: 0.9, active: true }
    ]
  },
  {
    id: 'sig-2',
    asset: 'ETHUSDT',
    direction: 'SHORT',
    entryPrice: 3450.25,
    stopLoss: 3550.00,
    takeProfit: 3250.00,
    confidence: 78,
    strategy: 'Mean Reversion',
    strategyId: 'strat-2',
    status: 'active',
    riskRewardRatio: 2.01,
    createdAt: subHours(new Date(), 5).toISOString(),
    closedAt: null,
    pnlPercent: null,
    drivers: [
      { label: 'Overbought on daily', weight: 0.7, active: true },
      { label: 'Bearish divergence', weight: 0.5, active: true }
    ]
  },
  {
    id: 'sig-3',
    asset: 'SOLUSDT',
    direction: 'LONG',
    entryPrice: 142.30,
    stopLoss: 138.50,
    takeProfit: 155.00,
    confidence: 85,
    strategy: 'Volatility Expansion',
    strategyId: 'strat-3',
    status: 'active',
    riskRewardRatio: 3.34,
    createdAt: subDays(new Date(), 1).toISOString(),
    closedAt: null,
    pnlPercent: null,
    drivers: [
      { label: 'Bollinger Band squeeze', weight: 0.9, active: true },
      { label: 'Moving Average crossover', weight: 0.4, active: true }
    ]
  }
];

export const mockActiveSignals = mockSignals.filter(s => s.status === 'active');
