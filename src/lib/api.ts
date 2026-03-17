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
  CreatorVerificationStatus,
  ExternalSignal,
  WebhookEvent,
  SignalIngestionRule
} from './types';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data?.detail === 'string') {
        message = data.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Institutional Data API
 * 
 * Provides a unified interface for data retrieval, 
 * abstracting the source (Mock vs Firestore).
 */
export const api = {
  user: {
    getProfile: async (userId: string): Promise<UserProfile> => {
      return request<UserProfile>(`/api/frontend/user/${userId}/profile`);
    },
    getKYC: async (userId: string): Promise<KYCStatus> => {
      return request<KYCStatus>(`/api/frontend/user/${userId}/kyc`);
    },
    getRiskScore: async (userId: string): Promise<RiskScore> => {
      return request<RiskScore>(`/api/frontend/user/${userId}/risk-score`);
    },
  },
  market: {
    getTickers: async (): Promise<MarketTicker[]> => {
      return request<MarketTicker[]>('/api/frontend/market/tickers');
    },
    getSentiment: async (): Promise<MarketSentiment> => {
      return request<MarketSentiment>('/api/frontend/market/sentiment');
    },
    getFundingRates: async (): Promise<FundingRate[]> => {
      return request<FundingRate[]>('/api/frontend/market/funding-rates');
    },
    getOpenInterest: async (): Promise<OpenInterest[]> => {
      return request<OpenInterest[]>('/api/frontend/market/open-interest');
    },
    getOnChainActivity: async (): Promise<OnChainActivity[]> => {
      return request<OnChainActivity[]>('/api/frontend/market/on-chain-activity');
    },
    getLiquidationClusters: async (): Promise<LiquidationCluster[]> => {
      return request<LiquidationCluster[]>('/api/frontend/market/liquidation-clusters');
    },
    getDataQuality: async (): Promise<MarketDataQuality[]> => {
      return request<MarketDataQuality[]>('/api/frontend/market/data-quality');
    },
  },
  portfolio: {
    getSummary: async (userId: string): Promise<PortfolioSummary> => {
      return request<PortfolioSummary>(`/api/frontend/portfolio/${userId}/summary`);
    },
    getPositions: async (userId: string): Promise<Position[]> => {
      return request<Position[]>(`/api/frontend/portfolio/${userId}/positions`);
    },
    getTrades: async (userId: string): Promise<Trade[]> => {
      return request<Trade[]>(`/api/frontend/portfolio/${userId}/trades`);
    },
    getPerformancePoints: async (userId: string): Promise<PerformancePoint[]> => {
      return request<PerformancePoint[]>(`/api/frontend/portfolio/${userId}/performance-points`);
    },
  },
  strategies: {
    getUserStrategies: async (userId: string): Promise<Strategy[]> => {
      return request<Strategy[]>(`/api/frontend/strategies/user/${userId}`);
    },
    getMarketplaceStrategies: async (): Promise<MarketplaceStrategy[]> => {
      return request<MarketplaceStrategy[]>('/api/frontend/strategies/marketplace');
    },
    getPerformance: async (id: string) => {
      try {
        return await request(`/api/frontend/strategies/${id}/performance`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    getStrategyPaperTradeResult: async (id: string) => {
      try {
        return await request(`/api/frontend/strategies/${id}/paper-trade-result`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
  },
  signals: {
    getLiveSignals: async (userId: string): Promise<Signal[]> => {
      return request<Signal[]>(`/api/frontend/signals/live/${userId}`);
    },
    getSignalDetail: async (id: string): Promise<Signal | null> => {
      try {
        return await request<Signal>(`/api/frontend/signals/${id}`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    getSignalProof: async (id: string): Promise<SignalProof | null> => {
      try {
        return await request<SignalProof>(`/api/frontend/signals/${id}/proof`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
  },
  external: {
    getSignals: async (userId: string): Promise<ExternalSignal[]> => {
      return request<ExternalSignal[]>(`/api/frontend/external/${userId}/signals`);
    },
    getWebhookEvents: async (userId: string): Promise<WebhookEvent[]> => {
      return request<WebhookEvent[]>(`/api/frontend/external/${userId}/webhook-events`);
    },
    getIngestionRule: async (userId: string): Promise<SignalIngestionRule> => {
      return request<SignalIngestionRule>(`/api/frontend/external/${userId}/ingestion-rule`);
    }
  },
  creator: {
    getVerificationPipeline: async (userId: string): Promise<CreatorVerificationStatus[]> => {
      return request<CreatorVerificationStatus[]>(`/api/frontend/creator/${userId}/verification-pipeline`);
    }
  },
  system: {
    getAuditLogs: async (userId: string): Promise<AuditLogEntry[]> => {
      return request<AuditLogEntry[]>(`/api/frontend/system/${userId}/audit-logs`);
    },
    getModelPerformance: async (): Promise<ModelPerformance[]> => {
      return request<ModelPerformance[]>('/api/frontend/system/model-performance');
    },
    getNotifications: async (userId: string): Promise<Notification[]> => {
      return request<Notification[]>(`/api/frontend/system/${userId}/notifications`);
    },
  },
};
