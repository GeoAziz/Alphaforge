import { Position } from '@/lib/types';

export const mockPositions: Position[] = [
  {
    id: 'pos-1',
    userId: 'u-12345',
    asset: 'BTCUSDT',
    direction: 'LONG',
    entryPrice: 66400,
    currentPrice: 68420.50,
    quantity: 0.5,
    unrealizedPnl: 1010.25,
    unrealizedPnlPercent: 3.04,
    riskExposure: 5.2,
    signalId: 'sig-1',
    openedAt: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: 'pos-2',
    userId: 'u-12345',
    asset: 'SOLUSDT',
    direction: 'LONG',
    entryPrice: 135.20,
    currentPrice: 142.30,
    quantity: 50,
    unrealizedPnl: 355,
    unrealizedPnlPercent: 5.25,
    riskExposure: 2.8,
    signalId: 'sig-3',
    openedAt: new Date(Date.now() - 172800000).toISOString()
  }
];