export type SignalDirection = 'LONG' | 'SHORT'
export type SignalStatus = 'active' | 'closed' | 'expired' | 'cancelled'

export interface Signal {
  id: string
  asset: string
  direction: SignalDirection
  entryPrice: number
  stopLoss: number
  takeProfit: number
  confidence: number
  strategy: string
  strategyId: string
  status: SignalStatus
  riskRewardRatio: number
  createdAt: string
  closedAt: string | null
  pnlPercent: number | null
  drivers: SignalDriver[]
}

export interface SignalDriver {
  label: string
  weight: number
  active: boolean
}

export interface PortfolioSummary {
  totalEquity: number
  unrealizedPnl: number
  realizedPnl: number
  totalTrades: number
  openPositions: number
  marginUsed: number
}

export interface Position {
  id: string
  asset: string
  direction: SignalDirection
  entryPrice: number
  currentPrice: number
  quantity: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  riskExposure: number
  signalId: string
  openedAt: string
}

export interface Trade {
  id: string
  asset: string
  direction: SignalDirection
  entryPrice: number
  exitPrice: number
  pnl: number
  pnlPercent: number
  status: 'win' | 'loss'
  strategy: string
  signalId: string
  executedAt: string
  closedAt: string
}

export interface MarketTicker {
  asset: string
  price: number
  change24h: number
  change24hAbs: number
  volume24h: number
  high24h: number
  low24h: number
}

export interface Strategy {
  id: string
  name: string
  description: string
  winRate: number
  avgRoi: number
  maxDrawdown: number
  sharpeRatio: number
  totalTrades: number
  profitFactor: number
  riskLevel: 'Low' | 'Medium' | 'High'
  isActive: boolean
}
