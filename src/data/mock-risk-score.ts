import { RiskScore } from '@/lib/types';

export const mockRiskScore: RiskScore = {
  userId: 'u-12345',
  score: 42,
  label: 'Medium',
  factors: {
    volatility: 35,
    leverage: 15,
    concentration: 50
  },
  updatedAt: new Date().toISOString()
};
