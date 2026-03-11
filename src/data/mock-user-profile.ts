import { UserProfile } from '@/lib/types';

export const mockUserProfile: UserProfile = {
  id: 'u-12345',
  name: 'Institutional Node 01',
  email: 'trader@alphaforge.ai',
  plan: 'Institutional',
  riskTolerance: 'balanced',
  connectedExchanges: ['Binance', 'Bybit', 'OKX'],
  onboardingComplete: true,
  createdAt: new Date().toISOString()
};