import { ModelPerformance } from '@/lib/types';

export const mockModelPerformances: ModelPerformance[] = [
  { id: 'm-1', modelName: 'AlphaEngine V4', accuracy: 84.2, latency: 12.4, uptime: 99.99, lastTraining: '2024-02-28T00:00:00Z' },
  { id: 'm-2', modelName: 'SentimentBERT', accuracy: 78.5, latency: 45.2, uptime: 99.95, lastTraining: '2024-03-01T00:00:00Z' }
];
