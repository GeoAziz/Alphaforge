import { 
  mockUserProfile, 
  mockTickers, 
  mockSentiment, 
  mockPortfolioSummary, 
  mockPositions, 
  mockTrades, 
  mockUserStrategies, 
  mockMarketplaceStrategies 
} from '@/data/mock-user-profile';
// Note: In a real implementation, we'd import all from their respective files.
// For brevity here, assuming they are available or imported.

import { 
  UserProfile, 
  MarketTicker, 
  MarketSentiment, 
  PortfolioSummary, 
  Position, 
  Trade, 
  Strategy, 
  MarketplaceStrategy,
  Signal,
  Notification
} from './types';
import { mockSignals } from '@/data/mock-signals';

/**
 * Institutional Data API
 * 
 * Provides a unified interface for data retrieval, 
 * abstracting the source (Mock vs Firestore).
 */
export const api = {
  user: {
    getProfile: async (userId: string): Promise<UserProfile> => {
      return mockUserProfile;
    },
  },
  market: {
    getTickers: async (): Promise<MarketTicker[]> => {
      return mockTickers;
    },
    getSentiment: async (): Promise<MarketSentiment> => {
      return mockSentiment;
    },
  },
  portfolio: {
    getSummary: async (userId: string): Promise<PortfolioSummary> => {
      return mockPortfolioSummary;
    },
    getPositions: async (userId: string): Promise<Position[]> => {
      return mockPositions;
    },
    getTrades: async (userId: string): Promise<Trade[]> => {
      return mockTrades;
    },
  },
  strategies: {
    getUserStrategies: async (userId: string): Promise<Strategy[]> => {
      return mockUserStrategies;
    },
    getMarketplaceStrategies: async (): Promise<MarketplaceStrategy[]> => {
      return mockMarketplaceStrategies;
    },
  },
  signals: {
    getLiveSignals: async (userId: string): Promise<Signal[]> => {
      return mockSignals;
    },
  },
};
