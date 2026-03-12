import { ExternalSignal, WebhookEvent, SignalIngestionRule } from '@/lib/types';
import { subMinutes, subHours } from 'date-fns';

export const mockExternalSignals: ExternalSignal[] = [
  {
    id: 'ext-sig-1',
    source: 'tradingview',
    asset: 'BTCUSDT',
    direction: 'LONG',
    confidence: 87,
    timestamp: subMinutes(new Date(), 12).toISOString(),
    webhookPayload: { symbol: 'BINANCE:BTCUSDT', direction: 'LONG', confidence: 0.87, strategy: 'RSI_Divergence' },
    status: 'executed',
    executionContext: {
      riskMultiplier: 1.0,
      positionSize: 520,
      executedAt: subMinutes(new Date(), 11).toISOString(),
      orderId: 'ord-9921'
    }
  },
  {
    id: 'ext-sig-2',
    source: 'tradingview',
    asset: 'ETHUSDT',
    direction: 'SHORT',
    confidence: 45,
    timestamp: subMinutes(new Date(), 45).toISOString(),
    webhookPayload: { symbol: 'BINANCE:ETHUSDT', direction: 'SHORT', confidence: 0.45, strategy: 'Trend_Flip' },
    status: 'rejected',
    rejectionReason: 'Confidence 45% below 70% threshold'
  },
  {
    id: 'ext-sig-3',
    source: 'tradingview',
    asset: 'SOLUSDT',
    direction: 'LONG',
    confidence: 92,
    timestamp: subHours(new Date(), 2).toISOString(),
    webhookPayload: { symbol: 'BINANCE:SOLUSDT', direction: 'LONG', confidence: 0.92, strategy: 'Breakout_v2' },
    status: 'processed'
  }
];

export const mockWebhookEvents: WebhookEvent[] = [
  {
    id: 'wh-1',
    userId: 'u-12345',
    timestamp: subMinutes(new Date(), 12).toISOString(),
    sourceIp: '52.89.214.238',
    signatureValid: true,
    payload: { symbol: 'BINANCE:BTCUSDT', direction: 'LONG', confidence: 0.87 },
    processingStatus: 'processed',
    matchedSignalId: 'ext-sig-1'
  },
  {
    id: 'wh-2',
    userId: 'u-12345',
    timestamp: subMinutes(new Date(), 45).toISOString(),
    sourceIp: '52.89.214.238',
    signatureValid: true,
    payload: { symbol: 'BINANCE:ETHUSDT', direction: 'SHORT', confidence: 0.45 },
    processingStatus: 'processed',
    matchedSignalId: 'ext-sig-2'
  },
  {
    id: 'wh-3',
    userId: 'u-12345',
    timestamp: subHours(new Date(), 3).toISOString(),
    sourceIp: '192.168.1.1',
    signatureValid: false,
    payload: { test: 'ping' },
    processingStatus: 'failed',
    errorMessage: 'Invalid HMAC signature'
  }
];

export const mockIngestionRule: SignalIngestionRule = {
  id: 'rule-1',
  userId: 'u-12345',
  minConfidence: 70,
  autoExecute: false,
  cooldownSeconds: 60,
  maxPositionsOpen: 5,
  riskMultiplier: 1.0,
  createdAt: subHours(new Date(), 24).toISOString(),
  updatedAt: subHours(new Date(), 2).toISOString()
};
