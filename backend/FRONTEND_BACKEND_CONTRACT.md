# Frontend ↔ Backend Contract (Pre-Wiring)

This document defines backend endpoints that satisfy the current frontend API surface in `src/lib/api.ts`.

## User
- `getProfile(userId)` → `GET /api/frontend/user/{user_id}/profile`
- `getKYC(userId)` → `GET /api/frontend/user/{user_id}/kyc`
- `getRiskScore(userId)` → `GET /api/frontend/user/{user_id}/risk-score`

## Market
- `getTickers()` → `GET /api/frontend/market/tickers`
- `getSentiment()` → `GET /api/frontend/market/sentiment`
- `getFundingRates()` → `GET /api/frontend/market/funding-rates`
- `getOpenInterest()` → `GET /api/frontend/market/open-interest`
- `getOnChainActivity()` → `GET /api/frontend/market/on-chain-activity`
- `getLiquidationClusters()` → `GET /api/frontend/market/liquidation-clusters`
- `getDataQuality()` → `GET /api/frontend/market/data-quality`

## Portfolio
- `getSummary(userId)` → `GET /api/frontend/portfolio/{user_id}/summary`
- `getPositions(userId)` → `GET /api/frontend/portfolio/{user_id}/positions`
- `getTrades(userId)` → `GET /api/frontend/portfolio/{user_id}/trades`
- `getPerformancePoints(userId)` → `GET /api/frontend/portfolio/{user_id}/performance-points`

## Strategies
- `getUserStrategies(userId)` → `GET /api/frontend/strategies/user/{user_id}`
- `getMarketplaceStrategies()` → `GET /api/frontend/strategies/marketplace`
- `getPerformance(id)` → `GET /api/frontend/strategies/{strategy_id}/performance`
- `getStrategyPaperTradeResult(id)` → `GET /api/frontend/strategies/{strategy_id}/paper-trade-result`

## Signals
- `getLiveSignals(userId)` → `GET /api/frontend/signals/live/{user_id}`
- `getSignalDetail(id)` → `GET /api/frontend/signals/{signal_id}`
- `getSignalProof(id)` → `GET /api/frontend/signals/{signal_id}/proof`

## External
- `getSignals(userId)` → `GET /api/frontend/external/{user_id}/signals`
- `getWebhookEvents(userId)` → `GET /api/frontend/external/{user_id}/webhook-events`
- `getIngestionRule(userId)` → `GET /api/frontend/external/{user_id}/ingestion-rule`

## Creator
- `getVerificationPipeline(userId)` → `GET /api/frontend/creator/{user_id}/verification-pipeline`

## System
- `getAuditLogs(userId)` → `GET /api/frontend/system/{user_id}/audit-logs`
- `getModelPerformance()` → `GET /api/frontend/system/model-performance`
- `getNotifications(userId)` → `GET /api/frontend/system/{user_id}/notifications`

## Roadmap Compatibility Aliases
- `GET /api/signals/latest` (alias to `GET /api/signals`)
- `GET /api/portfolio/{user_id}/positions` (alias to `GET /api/positions/{user_id}`)
