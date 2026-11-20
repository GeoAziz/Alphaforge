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
  OnChainMetricDetail,
  LiquidationCluster,
  CreatorVerificationStatus,
  ExternalSignal,
  WebhookEvent,
  SignalIngestionRule,
  PaperTradeResult,
  MonitoringStats,
  ChatMessage,
  EducationContent
} from './types';

const getApiBaseUrl = (): string => {
  // If explicitly provided via env (e.g. external microservice or production domain)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  }
  // In the browser, use empty string so requests automatically route to current host origin (e.g. http://192.168.x.x:9002/api/...)
  if (typeof window !== 'undefined') {
    return '';
  }
  // Server-side rendering default to local backend
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getApiBaseUrl();

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function getAuthToken(): Promise<string | null> {
  try {
    const { auth } = await import('@/firebase').then(async (m) => {
      const sdk = m.initializeFirebase();
      return sdk;
    });
    const user = auth.currentUser;
    if (user) {
      return await user.getIdToken();
    }
  } catch (error) {
    console.warn('Failed to get auth token:', error);
  }
  return null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> || {}),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: 'include', // Include credentials for cross-origin requests
    headers,
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
    register: async (data: { firebase_uid: string; email: string; display_name?: string }): Promise<UserProfile> => {
      return request<UserProfile>('/api/users/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },
  settings: {
    saveRisk: async (data: { risk_level: string; position_size: number; max_leverage: number }): Promise<{ success: boolean }> => {
      return request<{ success: boolean }>('/api/settings/risk', {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },
  },
  exchange: {
    connect: async (data: { exchange: string; api_key: string; api_secret: string }): Promise<{ success: boolean; id?: string }> => {
      return request<{ success: boolean; id?: string }>('/api/exchange/connect', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    disconnect: async (exchangeId: string): Promise<{ success: boolean }> => {
      return request<{ success: boolean }>('/api/exchange/disconnect', {
        method: 'POST',
        body: JSON.stringify({ exchange_id: exchangeId }),
      });
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
    getOnChainMetrics: async (): Promise<OnChainMetricDetail[]> => {
      return request<OnChainMetricDetail[]>('/api/frontend/market/on-chain-metrics');
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
    getStrategyPaperTradeResult: async (id: string): Promise<PaperTradeResult | null> => {
      try {
        return await request<PaperTradeResult>(`/api/frontend/strategies/${id}/paper-trade-result`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    subscribe: async (strategyId: string, userId: string): Promise<{ success: boolean }> => {
      return request<{ success: boolean }>(`/api/strategies/${strategyId}/subscribe`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      });
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
    execute: async (signalId: string, userId: string): Promise<{ success: boolean; trade_id?: string }> => {
      return request<{ success: boolean; trade_id?: string }>(`/api/signals/${signalId}/execute`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      });
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
  academy: {
    listContent: async (category?: string, difficulty?: string): Promise<{ success: boolean; content: EducationContent[]; total: number }> => {
      const params = new URLSearchParams();
      if (category) params.set('category', category);
      if (difficulty) params.set('difficulty', difficulty);
      const qs = params.toString();
      return request(`/api/academy/content${qs ? `?${qs}` : ''}`);
    },
    getProgress: async (userId: string): Promise<{
      success: boolean;
      progress: { content_id: string; completed: boolean; quiz_score: number | null }[];
      completed_count: number;
      total_content: number;
      completion_pct: number;
    }> => {
      return request(`/api/academy/progress/${encodeURIComponent(userId)}`);
    },
    markCompleted: async (userId: string, contentId: string, quizScore?: number): Promise<{ success: boolean }> => {
      return request(`/api/academy/progress/${encodeURIComponent(contentId)}`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, quiz_score: quizScore ?? null }),
      });
    },
  },
  backtest: {
    run: async (userId: string, config: { name?: string; symbols?: string[]; initial_capital?: number; parameters?: Record<string, unknown> }): Promise<{
      success: boolean;
      backtest_id: string;
      results: {
        data_source: string;
        error?: string;
        symbol?: string;
        candles_used?: number;
        equity_curve: { day: number; equity: number; date: string }[];
        metrics: Record<string, number | string>;
        trades: unknown[];
      };
    }> => {
      return request(`/api/backtest/run?user_id=${encodeURIComponent(userId)}`, {
        method: 'POST',
        body: JSON.stringify(config),
      });
    },
  },
  tournaments: {
    listTournaments: async (status?: string, limit?: number) => {
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      if (limit) params.set('limit', String(limit));
      const qs = params.toString();
      return request(`/api/tournaments${qs ? `?${qs}` : ''}`);
    },
    joinTournament: async (tournamentId: string, userId: string) => {
      return request(`/api/tournaments/${encodeURIComponent(tournamentId)}/join?user_id=${encodeURIComponent(userId)}`, {
        method: 'POST',
      });
    },
    getLeaderboard: async (tournamentId: string, sortBy?: string, limit?: number) => {
      const params = new URLSearchParams();
      if (sortBy) params.set('sort_by', sortBy);
      if (limit) params.set('limit', String(limit));
      const qs = params.toString();
      return request(`/api/tournaments/${encodeURIComponent(tournamentId)}/leaderboard${qs ? `?${qs}` : ''}`);
    },
    getMyStatus: async (tournamentId: string, userId: string) => {
      return request(`/api/tournaments/${encodeURIComponent(tournamentId)}/status?user_id=${encodeURIComponent(userId)}`);
    },
  },
  community: {
    getProfile: async (userId: string) => {
      return request(`/api/community/profile/${encodeURIComponent(userId)}`);
    },
    updateProfile: async (userId: string, data: { display_name?: string; bio?: string; avatar_url?: string }) => {
      return request(`/api/community/profile`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...data }),
      });
    },
    follow: async (targetUserId: string) => {
      return request(`/api/community/follow/${encodeURIComponent(targetUserId)}`, {
        method: 'POST',
      });
    },
    unfollow: async (targetUserId: string) => {
      return request(`/api/community/unfollow/${encodeURIComponent(targetUserId)}`, {
        method: 'POST',
      });
    },
    getLeaderboard: async (metric?: string, limit?: number) => {
      const params = new URLSearchParams();
      if (metric) params.set('metric', metric);
      if (limit) params.set('limit', String(limit));
      const qs = params.toString();
      return request(`/api/community/leaderboard${qs ? `?${qs}` : ''}`);
    },
    addComment: async (strategyId: string, comment: string) => {
      return request(`/api/community/strategy/${encodeURIComponent(strategyId)}/comment`, {
        method: 'POST',
        body: JSON.stringify(comment),
      });
    },
    rateStrategy: async (strategyId: string, rating: number) => {
      return request(`/api/community/strategy/${encodeURIComponent(strategyId)}/rate`, {
        method: 'POST',
        body: JSON.stringify(rating),
      });
    },
    getNotifications: async () => {
      return request(`/api/community/notifications`);
    },
  },
  compliance: {
    acceptAllDisclaimers: async (userId: string): Promise<{ success: boolean }> => {
      return request(`/api/compliance/disclaimers/accept-all?user_id=${encodeURIComponent(userId)}`, {
        method: 'POST',
      });
    },
    getDisclaimerStatus: async (userId: string): Promise<{ success: boolean; disclaimers: Record<string, { title: string; acknowledged: boolean; acknowledged_at: string | null }>; all_accepted: boolean }> => {
      return request(`/api/compliance/disclaimers/status?user_id=${encodeURIComponent(userId)}`);
    },
  },
  chat: {
    sendMessage: async (data: {
      user_id: string;
      message: string;
      signal_id?: string;
      strategy_id?: string;
      page_context?: string;
    }): Promise<{ success: boolean; ai_response: string; context_used: boolean; timestamp: string }> => {
      return request(`/api/chat/message`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    getHistory: async (userId: string, limit = 50): Promise<ChatMessage[]> => {
      const res = await request<{ success: boolean; messages: Array<{ id: string; role: string; message: string; created_at: string }> }>(
        `/api/chat/history?user_id=${encodeURIComponent(userId)}&limit=${limit}`
      );
      return (res.messages || []).map((m) => ({
        id: String(m.id),
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.message,
        timestamp: m.created_at,
      }));
    },
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
    getMonitoringStats: async (): Promise<MonitoringStats> => {
      return request<MonitoringStats>('/api/monitoring/stats');
    },
  },
};
