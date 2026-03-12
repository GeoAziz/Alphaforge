import { PerformancePoint, StrategyPerformance } from '@/lib/types';
import { subDays, format } from 'date-fns';

export const mockPerformancePoints: PerformancePoint[] = Array.from({ length: 30 }).map((_, i) => ({
  id: `pp-${i}`,
  userId: 'u-12345',
  date: format(subDays(new Date(), 30 - i), 'yyyy-MM-dd'),
  equity: 100000 + Math.random() * 50000,
  drawdown: Math.random() * 5,
  cumulativePnl: Math.random() * 20000
}));

export const mockStrategyPerformances: StrategyPerformance[] = [
  { id: 'strat-1', strategyName: 'Momentum Breakout', winRate: 68.4, roi: 12.4, trades: 1240, profitFactor: 2.15 },
  { id: 'strat-2', strategyName: 'Liquid Alpha Neutral', winRate: 84.2, roi: 4.5, trades: 8500, profitFactor: 3.84 }
];
