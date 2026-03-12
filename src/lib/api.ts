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
  Notification,
  PerformancePoint,
  KYCStatus,
  RiskScore,
  ModelPerformance,
  SignalProof,
  MarketDataQuality,
  AuditLogEntry,
  FundingRate,
  OpenInterest,
  OnChainActivity,
  LiquidationCluster,
  CreatorVerificationStatus
} from './types';

import { mockUserProfile } from '@/data/mock-user-profile';
import { 
  mockTickers, 
  mockSentiment, 
  mockFundingRates, 
  mockOpenInterest, 
  mockOnChainActivity, 
  mockLiquidationClusters 
} from '@/data/mock-market-data';
import { mockPortfolioSummary } from '@/data/mock-portfolio-summary';
import { mockPositions } from '@/data/mock-positions';
import { mockTrades } from '@/data/mock-trades';
import { mockUserStrategies, mockMarketplaceStrategies } from '@/data/mock-strategies';
import { mockSignals } from '@/data/mock-signals';
import { mockPerformancePoints, mockStrategyPerformances } from '@/data/mock-analytics';
import { mockAuditLogs } from '@/data/mock-audit-log';
import { mockKYCStatus } from '@/data/mock-kyc-status';
import { mockRiskScore } from '@/data/mock-risk-score';
import { mockModelPerformances } from '@/data/mock-model-performance';
import { mockSignalProofs } from '@/data/mock-signal-proof';
import { mockMarketDataQualities } from '@/data/mock-market-data-quality';

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
    getKYC: async (userId: string): Promise<KYCStatus> => {
      return mockKYCStatus;
    },
    getRiskScore: async (userId: string): Promise<RiskScore> => {
      return mockRiskScore;
    },
  },
  market: {
    getTickers: async (): Promise<MarketTicker[]> => {
      return mockTickers;
    },
    getSentiment: async (): Promise<MarketSentiment> => {
      return mockSentiment;
    },
    getFundingRates: async (): Promise<FundingRate[]> => {
      return mockFundingRates;
    },
    getOpenInterest: async (): Promise<OpenInterest[]> => {
      return mockOpenInterest;
    },
    getOnChainActivity: async (): Promise<OnChainActivity[]> => {
      return mockOnChainActivity;
    },
    getLiquidationClusters: async (): Promise<LiquidationCluster[]> => {
      return mockLiquidationClusters;
    },
    getDataQuality: async (): Promise<MarketDataQuality[]> => {
      return mockMarketDataQualities;
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
    getPerformancePoints: async (userId: string): Promise<PerformancePoint[]> => {
      return mockPerformancePoints;
    },
  },
  strategies: {
    getUserStrategies: async (userId: string): Promise<Strategy[]> => {
      return mockUserStrategies;
    },
    getMarketplaceStrategies: async (): Promise<MarketplaceStrategy[]> => {
      return mockMarketplaceStrategies;
    },
    getPerformance: async (id: string) => {
      return mockStrategyPerformances.find(p => p.id === id) || null;
    },
  },
  signals: {
    getLiveSignals: async (userId: string): Promise<Signal[]> => {
      return mockSignals;
    },
    getSignalDetail: async (id: string): Promise<Signal | null> => {
      return mockSignals.find(s => s.id === id) || null;
    },
    getSignalProof: async (id: string): Promise<SignalProof | null> => {
      const proof = mockSignalProofs.find(p => p.signalId === id);
      if (!proof) return null;
      return {
        ...proof,
        txHash: '0x' + Math.random().toString(16).slice(2, 10) + '...',
        hypothesis: 'The Momentum Breakout model detected an 84% volume spike on the 4H timeframe, corroborated by institutional buy walls on Coinbase.',
        backtestResult: 'Historical win rate of 68.4% over 1,200 simulated trades since 2022.',
        paperResults: 'Sub-10ms execution parity achieved over a 7-day verification period.',
        liveResults: 'Signal resolved with a +4.2% ROI within 12 hours of issuance.'
      };
    },
  },
  creator: {
    getVerificationPipeline: async (userId: string): Promise<CreatorVerificationStatus[]> => {
      return [
        {
          strategyId: 'ms-1',
          strategyName: 'Black Swan Defender',
          currentStage: 5,
          overallStatus: 'Active',
          steps: [
            { id: '1', name: 'Identity Audit', status: 'Completed', description: 'Institutional KYC/AML passed.' },
            { id: '2', name: 'Logic Review', status: 'Completed', description: 'Strategy code audit finalized.' },
            { id: '3', name: 'Backtest Verification', status: 'Completed', description: 'Simulated performance verified.' },
            { id: '4', name: 'Latency Handshake', status: 'Completed', description: 'Execution parity confirmed.' },
            { id: '5', name: 'Public Listing', status: 'Completed', description: 'Node is active in marketplace.' }
          ]
        },
        {
          strategyId: 'ms-4',
          strategyName: 'Funding Arbitrage',
          currentStage: 2,
          overallStatus: 'Review',
          steps: [
            { id: '1', name: 'Identity Audit', status: 'Completed', description: 'Institutional KYC passed.' },
            { id: '2', name: 'Logic Review', status: 'In Progress', description: 'Audit pending for cross-exchange arbitrage logic.' },
            { id: '3', name: 'Backtest Verification', status: 'Pending', description: 'Waiting for historical data sync.' },
            { id: '4', name: 'Latency Handshake', status: 'Pending', description: 'Awaiting node synchronization.' },
            { id: '5', name: 'Public Listing', status: 'Pending', description: 'Locked.' }
          ]
        }
      ];
    }
  },
  system: {
    getAuditLogs: async (userId: string): Promise<AuditLogEntry[]> => {
      return mockAuditLogs;
    },
    getModelPerformance: async (): Promise<ModelPerformance[]> => {
      return mockModelPerformances;
    },
    getNotifications: async (userId: string): Promise<Notification[]> => {
      return [
        {
          id: 'n-1',
          userId,
          type: 'system',
          title: 'Node Sync Initialized',
          message: 'Institutional handshake established with AF-NODE-US-01.',
          read: false,
          critical: false,
          createdAt: new Date().toISOString()
        }
      ];
    },
  },
};
