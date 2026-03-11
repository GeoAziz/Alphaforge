export type SignalDirection = 'LONG' | 'SHORT';
export type SignalStatus = 'active' | 'closed' | 'expired' | 'cancelled';
export type RiskLevel = 'Low' | 'Medium' | 'High';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  plan: string;
  riskTolerance: string;
  connectedExchanges: string[];
  onboardingComplete: boolean;
}

export interface PortfolioSummary {
  id: string;
  totalEquity: number;
  unrealizedPnl: number;
  realizedPnl: number;
  totalTrades: number;
  openPositions: number;
  marginUsed: number;
}

export interface Position {
  id: string;
  userId: string;
  asset: string;
  direction: SignalDirection;
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  riskExposure: number;
  signalId: string;
  openedAt: string;
}

export interface Trade {
  id: string;
  userId: string;
  asset: string;
  direction: SignalDirection;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPercent: number;
  status: 'win' | 'loss';
  strategy: string;
  signalId: string;
  executedAt: string;
  closedAt: string;
}

export interface Signal {
  id: string;
  asset: string;
  direction: SignalDirection;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  confidence: number;
  strategy: string;
  strategyId: string;
  status: SignalStatus;
  riskRewardRatio: number;
  createdAt: string;
  closedAt?: string;
  pnlPercent?: number;
  drivers: string[];
}

export interface MarketTicker {
  id: string;
  asset: string;
  price: number;
  change24h: number;
  change24hAbs: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  winRate: number;
  avgRoi: number;
  maxDrawdown: number;
  sharpeRatio: number;
  totalTrades: number;
  profitFactor: number;
  riskLevel: RiskLevel;
  isActive: boolean;
}

export interface MarketplaceStrategy {
  id: string;
  name: string;
  creator: string;
  description: string;
  winRate: number;
  roi: number;
  maxDrawdown: number;
  subscribers: number;
  riskLevel: RiskLevel;
  monthlyPrice: number;
  isVerified: boolean;
}

export interface MarketSentiment {
  id: string;
  score: number;
  label: string;
}

export interface Notification {
  id: string;
  userId: string;
  type: 'signal' | 'trade' | 'risk' | 'system';
  title: string;
  message: string;
  read: boolean;
  critical: boolean;
  createdAt: string;
}

export interface BacktestResult {
  id: string;
  userId: string;
  winRate: number;
  totalTrades: number;
  roi: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  profitFactor: number;
  equityCurvePointIds: string[];
}