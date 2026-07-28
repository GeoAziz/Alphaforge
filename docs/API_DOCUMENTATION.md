# AlphaForge API Documentation

## Overview

The AlphaForge API provides programmatic access to trading signals, portfolio management, market data, and more. All endpoints require authentication and return JSON responses.

**Base URL**: `https://api.alphaforge.com`  
**API Version**: v1  
**Authentication**: Bearer Token (Firebase JWT)

## Authentication

### Getting an API Token

1. Log in to AlphaForge dashboard
2. Go to **Settings** → **API Keys**
3. Click **Generate New Key**
4. Copy the token
5. Store securely (never commit to version control)

### Using the Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.alphaforge.com/api/signals
```

## Core Endpoints

### Signals API

#### Get All Signals
```http
GET /api/signals
```

**Response:**
```json
{
  "success": true,
  "signals": [
    {
      "id": "sig_123",
      "symbol": "BTC/USD",
      "signal_type": "BUY",
      "confidence": 0.85,
      "entry_price": 50000,
      "target_price": 52000,
      "stop_loss": 48000,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Top Signals
```http
GET /api/signals/top?limit=10
```

**Query Parameters:**
- `limit`: Number of signals to return (1-100, default: 10)

#### Process Signal
```http
POST /api/signals/process
Content-Type: application/json

{
  "symbol": "ETH/USD",
  "signal_type": "SELL",
  "confidence": 0.72
}
```

**Response:**
```json
{
  "success": true,
  "signal_id": "sig_456"
}
```

### Portfolio API

#### Get Portfolio Summary
```http
GET /api/portfolio/{user_id}
```

**Response:**
```json
{
  "success": true,
  "portfolio_value": 100000,
  "total_return": 5000,
  "return_percentage": 5.0,
  "positions": [],
  "cash": 50000
}
```

#### Get Portfolio Metrics
```http
GET /api/portfolio/{user_id}/metrics
```

**Response:**
```json
{
  "success": true,
  "sharpe_ratio": 1.5,
  "max_drawdown": -0.15,
  "win_rate": 0.65,
  "profit_factor": 1.8,
  "total_trades": 50
}
```

### Market Data API

#### Get Market Tickers
```http
GET /api/market/tickers?symbols=BTC,ETH,BNB
```

**Query Parameters:**
- `symbols`: Comma-separated list of symbols

**Response:**
```json
{
  "success": true,
  "tickers": [
    {
      "symbol": "BTC",
      "price": 52000,
      "change_24h": 2.5,
      "volume": 1000000000,
      "market_cap": 1020000000000
    }
  ]
}
```

#### Get Market Sentiment
```http
GET /api/market/sentiment
```

**Response:**
```json
{
  "bullish_count": 30,
  "bearish_count": 20,
  "neutral_count": 50,
  "bullish_pct": 30.0,
  "bearish_pct": 20.0,
  "neutral_pct": 50.0,
  "composite_score": 10.0,
  "market_status": "NEUTRAL"
}
```

### Forex API

#### Get Supported Forex Pairs
```http
GET /api/forex/pairs
```

**Response:**
```json
{
  "success": true,
  "pairs": [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CHF"
  ],
  "count": 4
}
```

#### Get Forex Ticker
```http
GET /api/forex/ticker/{pair}
```

**Example:** `GET /api/forex/ticker/EUR%2FUSD`

**Response:**
```json
{
  "success": true,
  "ticker": {
    "symbol": "EUR/USD",
    "price": 1.0850,
    "bid": 1.0849,
    "ask": 1.0851,
    "spread": 0.0002
  }
}
```

#### Get Forex OHLCV
```http
GET /api/forex/ohlcv/{pair}?interval=1h&limit=100
```

**Query Parameters:**
- `interval`: 1m, 5m, 15m, 1h, 4h, 1d
- `limit`: Number of candles (1-500, default: 100)

**Response:**
```json
{
  "success": true,
  "pair": "EUR/USD",
  "interval": "1h",
  "ohlcv": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "open": 1.0840,
      "high": 1.0860,
      "low": 1.0835,
      "close": 1.0850,
      "volume": 1000000
    }
  ],
  "count": 1
}
```

### Paper Trading API

#### Place Paper Trade
```http
POST /api/trades/paper
Content-Type: application/json

{
  "symbol": "BTC/USD",
  "side": "BUY",
  "quantity": 0.1,
  "entry_price": 50000,
  "take_profit": 52000,
  "stop_loss": 48000
}
```

**Response:**
```json
{
  "success": true,
  "trade_id": "trade_123",
  "status": "OPEN",
  "entry_time": "2024-01-15T10:30:00Z"
}
```

#### Get Paper Trades
```http
GET /api/trades/paper?status=OPEN&limit=50
```

**Query Parameters:**
- `status`: OPEN, CLOSED, ALL
- `limit`: Results per page (1-100)

### Backtesting API

#### Run Backtest
```http
POST /api/backtest/run
Content-Type: application/json

{
  "symbols": ["BTC"],
  "start_date": "2023-01-15T00:00:00Z",
  "end_date": "2024-01-15T00:00:00Z",
  "initial_capital": 100000,
  "parameters": {
    "min_confidence": 0.7
  }
}
```

**Response:**
```json
{
  "success": true,
  "backtest_id": "backtest_123",
  "status": "completed",
  "results": {
    "total_return": "12.5%",
    "total_trades": 45,
    "win_rate": "64.4%"
  }
}
```

#### Get Backtest Results
```http
GET /api/backtest/{backtest_id}
```

**Response:**
```json
{
  "success": true,
  "backtest": {
    "id": "backtest_123",
    "status": "completed",
    "results": {
      "equity_curve": [...],
      "metrics": {...},
      "trades": [...]
    }
  }
}
```

## Error Handling

All errors return appropriate HTTP status codes and error messages:

```json
{
  "success": false,
  "error": "Insufficient data for backtest"
}
```

**Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Rate Limited
- `500`: Server Error

## Rate Limiting

API requests are rate limited:
- **Free tier**: 100 requests/hour
- **Pro tier**: 10,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1642262400
```

## Webhooks

Subscribe to real-time events:

```http
POST /api/webhooks/subscribe
Content-Type: application/json

{
  "url": "https://yourserver.com/webhook",
  "events": ["signal.created", "trade.closed", "alert.triggered"]
}
```

**Webhook Events:**
- `signal.created`: New signal generated
- `trade.closed`: Trade position closed
- `alert.triggered`: Risk alert triggered
- `backtest.completed`: Backtest finished

## Code Examples

### Python
```python
import requests

API_URL = "https://api.alphaforge.com"
TOKEN = "your_api_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get signals
response = requests.get(
    f"{API_URL}/api/signals",
    headers=headers
)
signals = response.json()["signals"]

# Place paper trade
trade_data = {
    "symbol": "BTC/USD",
    "side": "BUY",
    "quantity": 0.1
}
response = requests.post(
    f"{API_URL}/api/trades/paper",
    json=trade_data,
    headers=headers
)
print(response.json())
```

### JavaScript
```javascript
const API_URL = "https://api.alphaforge.com";
const TOKEN = "your_api_token";

const headers = {
  "Authorization": `Bearer ${TOKEN}`,
  "Content-Type": "application/json"
};

// Get forex pairs
fetch(`${API_URL}/api/forex/pairs`, { headers })
  .then(res => res.json())
  .then(data => console.log(data.pairs));

// Run backtest
const backtest = {
  symbols: ["BTC"],
  start_date: "2023-01-15T00:00:00Z",
  end_date: "2024-01-15T00:00:00Z",
  initial_capital: 100000
};

fetch(`${API_URL}/api/backtest/run`, {
  method: "POST",
  headers,
  body: JSON.stringify(backtest)
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Support

- **Documentation**: https://docs.alphaforge.com
- **Status Page**: https://status.alphaforge.com
- **Email**: api-support@alphaforge.com
- **Discord**: https://discord.gg/alphaforge
