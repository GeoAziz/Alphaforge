import { Trade } from '@/lib/types';

export const mockTrades: Trade[] = [
  {
    id: 't-1',
    userId: 'u-12345',
    asset: 'ETHUSDT',
    direction: 'SHORT',
    entryPrice: 3600,
    exitPrice: 3450,
    pnl: 150,
    pnlPercent: 4.16,
    status: 'win',
    strategy: 'Mean Reversion',
    signalId: 'sig-prev-1',
    executedAt: new Date(Date.now() - 259200000).toISOString(),
    closedAt: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: 't-2',
    userId: 'u-12345',
    asset: 'BTCUSDT',
    direction: 'LONG',
    entryPrice: 62000,
    exitPrice: 64500,
    pnl: 2500,
    pnlPercent: 4.03,
    status: 'win',
    strategy: 'Momentum Breakout',
    signalId: 'sig-prev-2',
    executedAt: new Date(Date.now() - 604800000).toISOString(),
    closedAt: new Date(Date.now() - 432000000).toISOString()
  }
];