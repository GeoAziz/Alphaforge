export type SignalDirection = 'LONG' | 'SHORT';
export type SignalStatus = 'active' | 'closed' | 'expired' | 'cancelled';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type NotificationType = 'signal' | 'trade' | 'risk' | 'system';
export type TradeStatus = 'win' | 'loss';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  plan: string;
  riskTolerance: string;
  connectedExchanges: string[];
  onboardingComplete: boolean;
  createdAt?: string;
  kycStatus?: 'Unverified' | 'Pending' | 'Verified' | 'Rejected';
}

export interface ConnectedExchange {
  id: string;
  exchange: string;
  connected: boolean;
  connectedAt: string;
  permissions: string[];
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
  status: TradeStatus;
  strategy: string;
  signalId: string;
  executedAt: string;
  closedAt: string;
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

export interface FundingRate {
  id: string;
  asset: string;
  exchange: string;
  rate: number;
  nextFundingTime: string;
}

export interface OpenInterest {
  id: string;
  asset: string;
  value: number;
  change24h: number;
}

export interface MarketSentiment {
  id: string;
  score: number;
  label: string;
  factors?: {
    social: number;
    volatility: number;
    orderBook: number;
  };
}

export interface OnChainActivity {
  id: string;
  type: 'whale_move' | 'exchange_flow' | 'contract_deploy';
  asset: string;
  amount: number;
  valueUsd: number;
  from: string;
  to: string;
  timestamp: string;
}

export interface LiquidationCluster {
  asset: string;
  value: number;
  type: 'long' | 'short';
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
  maxLeverage?: number;
  signals?: number;
  status?: string;
  createdAt?: string;
}

export interface PaperTradeResult {
  duration: number;
  signalCount: number;
  roi: number;
  maxDrawdown: number;
  sharpeRatio: number;
  vsBacktestDelta: number;
  passed: boolean;
  completedAt: string;
}

export interface PerformancePoint {
  id: string;
  userId: string;
  strategyId?: string;
  backtestResultId?: string;
  date: string;
  equity: number;
  drawdown: number;
  cumulativePnl: number;
}

export interface StrategyPerformance {
  id: string;
  strategyName: string;
  winRate: number;
  roi: number;
  trades: number;
  profitFactor: number;
}

export interface Notification {
  id: string;
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  critical: boolean;
  createdAt: string;
}

export interface BacktestConfig {
  id: string;
  userId: string;
  asset: string;
  strategyId: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  riskPerTrade: number;
}

export interface BacktestResult {
  id: string;
  userId: string;
  backtestConfigId: string;
  winRate: number;
  totalTrades: number;
  roi: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  profitFactor: number;
  equityCurvePointIds: string[];
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
  reputationScore: number;
  verificationStage: number; // 1-5
  sharpeRatio: number;
  performanceBadge?: 'New' | 'Trending' | 'Best in Category';
  paperTradeDelta?: number; // e.g., +0.5% (difference between paper and backtest)
  pricingModel: 'Subscription' | 'Profit Share';
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
  drivers: SignalDriver[];
}

export interface SignalDriver {
  label: string;
  weight: number;
  active: boolean;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  target: string;
  userId: string;
  status: 'Success' | 'Authorized' | 'Warning' | 'Failure';
  node: string;
}

export interface KYCStatus {
  userId: string;
  status: 'Unverified' | 'Pending' | 'Verified' | 'Rejected';
  level: 1 | 2 | 3;
  verifiedAt?: string;
}

export interface RiskScore {
  userId: string;
  score: number;
  label: 'Low' | 'Medium' | 'High';
  factors: {
    volatility: number;
    leverage: number;
    concentration: number;
  };
  updatedAt: string;
}

export interface ModelPerformance {
  id: string;
  modelName: string;
  accuracy: number;
  latency: number;
  uptime: number;
  lastTraining: string;
}

export interface SignalProof {
  signalId: string;
  hash: string;
  merkleRoot: string;
  timestamp: string;
  verified: boolean;
  txHash?: string;
  hypothesis?: string;
  backtestResult?: string;
  paperResults?: string;
  liveResults?: string;
}

export interface MarketDataQuality {
  asset: string;
  source: string;
  freshness: number;
  status: 'Optimal' | 'Degraded' | 'Offline';
}

export interface TrendIndicator {
  asset: string;
  strength: number; // 0-100
  bias: 'Bullish' | 'Bearish' | 'Neutral';
  ma20: number;
  ma50: number;
  ma200: number;
}

export interface SocialSentimentDetail {
  asset: string;
  score: number;
  sources: {
    name: string;
    weight: number;
    sentiment: 'Bullish' | 'Bearish' | 'Neutral';
  }[];
}

export interface OnChainMetricDetail {
  asset: string;
  name: string;
  value: string;
  status: 'Overvalued' | 'Undervalued' | 'Neutral';
  change24h: number;
}

export interface StrategyVerificationStep {
  id: string;
  name: string;
  status: 'Pending' | 'In Progress' | 'Completed' | 'Rejected';
  description: string;
  timestamp?: string;
}

export interface CreatorVerificationStatus {
  strategyId: string;
  strategyName: string;
  currentStage: number;
  steps: StrategyVerificationStep[];
  overallStatus: 'Active' | 'Review' | 'Denied';
}

export interface ExternalSignal {
  id: string;
  source: 'tradingview';
  asset: string;
  direction: SignalDirection;
  confidence?: number;
  timestamp: string;
  webhookPayload: Record<string, any>;
  status: 'received' | 'validated' | 'processed' | 'executed' | 'rejected';
  rejectionReason?: string;
  executionContext?: {
    riskMultiplier: number;
    positionSize: number;
    executedAt: string;
    orderId?: string;
  };
}

export interface SignalIngestionRule {
  id: string;
  userId: string;
  minConfidence: number;
  autoExecute: boolean;
  cooldownSeconds: number;
  maxPositionsOpen: number;
  riskMultiplier: number;
  createdAt: string;
  updatedAt: string;
}

export interface WebhookEvent {
  id: string;
  userId: string;
  timestamp: string;
  sourceIp?: string;
  signatureValid: boolean;
  payload: Record<string, any>;
  processingStatus: 'pending' | 'processed' | 'failed';
  errorMessage?: string;
  matchedSignalId?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: ChatAction[];
}

export interface ChatAction {
  label: string;
  type: 'copy_strategy' | 'view_backtest' | 'view_signal' | 'trade' | 'link';
  targetId?: string;
  url?: string;
}
