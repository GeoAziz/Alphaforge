# Frontend Integration Guide - Recommendation Services

This guide shows how to integrate the 6 new recommendation system endpoints into your Next.js frontend.

## 🎯 Available Endpoints

### 1. Signal Performance Endpoints

#### Get High-Performing Signals
```
GET /api/signals/high-performers?limit=10&min_executions=5
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "high_performers": [
    {
      "signal_id": "sig_001",
      "num_times_executed": 12,
      "win_rate": 0.75,
      "total_roi_pct": 18.5,
      "total_pnl": 2100,
      "is_high_performer": true
    }
  ],
  "min_executions_filter": 5
}
```

**Integration Example (React Hook):**
```typescript
import { useCallback, useState } from 'react';

export function useHighPerformingSignals() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const fetchHighPerformers = useCallback(async (limit = 10) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/signals/high-performers?limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${await getAuthToken()}`
          }
        }
      );
      const data = await response.json();
      setSignals(data.high_performers);
    } catch (error) {
      console.error('Failed to fetch high performers:', error);
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { signals, loading, fetchHighPerformers };
}
```

### 2. External Signal Validation Endpoints

#### Get All External Signal Sources
```
GET /api/external-signals/sources
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "sources": [
    {
      "external_source": "tradingview",
      "executed_win_rate": 0.68,
      "total_pnl": 1250,
      "total_signals_executed": 25,
      "reliability_score": 0.82,
      "recommendation": "HIGHLY_TRUSTED"
    }
  ]
}
```

**UI Component Example:**
```typescript
export function ExternalSignalSourcesList() {
  const { signals, loading } = useHighPerformingSignals();
  
  return (
    <div className="space-y-4">
      <h2>Trusted Signal Sources</h2>
      {loading ? (
        <div>Loading...</div>
      ) : (
        signals.map(source => (
          <div key={source.external_source} className="border rounded p-4">
            <div className="flex justify-between items-center">
              <span className="font-semibold">{source.external_source}</span>
              <span className={`px-3 py-1 rounded text-sm ${
                source.recommendation === 'HIGHLY_TRUSTED' 
                  ? 'bg-green-100 text-green-800'
                  : source.recommendation === 'RELIABLE'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {source.recommendation}
              </span>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              <p>Win Rate: {(source.executed_win_rate * 100).toFixed(1)}%</p>
              <p>Total PnL: ${source.total_pnl}</p>
              <p>Signals Executed: {source.total_signals_executed}</p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
```

### 3. Market Correlation Analysis Endpoints

#### Get Market Correlations
```
GET /api/market/correlations?time_window=30d
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "success": true,
  "time_window": "30d",
  "lookback_days": 30,
  "correlations": {
    "BTC/ETH": {
      "asset1": "BTC",
      "asset2": "ETH",
      "correlation_1d": 0.85,
      "correlation_7d": 0.89,
      "correlation_30d": 0.93,
      "divergence_detected": false,
      "divergence_strength": 0.0
    }
  }
}
```

**Hook for Correlation Matrix:**
```typescript
export function useMarketCorrelations(timeWindow = '30d') {
  const [correlations, setCorrelations] = useState({});
  
  useEffect(() => {
    fetch(`/api/market/correlations?time_window=${timeWindow}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setCorrelations(data.correlations));
  }, [timeWindow]);
  
  return correlations;
}
```

### 4. Signal Conflict Detection

#### Check Signal Conflicts
```
POST /api/market/signals/conflicts
Authorization: Bearer <firebase_token>
Content-Type: application/json

{
  "asset": "BTC",
  "signal_type": "BUY",
  "related_assets": ["ETH", "SOL", "BNB"]
}
```

**Response:**
```json
{
  "success": true,
  "asset": "BTC",
  "signal_type": "BUY",
  "has_conflicts": false,
  "conflict_details": {
    "conflicts": []
  }
}
```

**Warning Component:**
```typescript
export function SignalConflictWarning({ asset, signalType }) {
  const [conflicts, setConflicts] = useState(null);
  
  useEffect(() => {
    fetch('/api/market/signals/conflicts', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        asset,
        signal_type: signalType,
        related_assets: ['ETH', 'SOL', 'BNB', 'XRP']
      })
    })
      .then(r => r.json())
      .then(data => setConflicts(data));
  }, [asset, signalType]);
  
  if (!conflicts?.has_conflicts) return null;
  
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
      <p className="font-semibold text-yellow-800">⚠️ Signal Conflict Detected</p>
      <ul className="mt-2 text-sm">
        {conflicts.conflict_details.conflicts?.map(c => (
          <li key={c.related_asset}>
            {c.related_asset}: {c.risk_level} risk ({c.correlation.toFixed(2)} correlation)
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 5. Cache Statistics

#### Get Cache Stats
```
GET /api/cache/stats
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "cache_stats": {
    "user_id": "user_123",
    "total_entries": 245,
    "active_entries": 238,
    "expired_entries": 7
  }
}
```

### 6. WebSocket Status

#### Get WebSocket Connection Status
```
GET /api/websocket/status
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "success": true,
  "websocket_enabled": true,
  "status": {
    "connected": true,
    "reconnect_attempts": 0,
    "subscribed_channels": 6,
    "active_subscriptions": ["ticker", "klines", "mark_price"]
  }
}
```

## 📊 Complete Dashboard Integration

```typescript
export function RecommendationDashboard() {
  const [tab, setTab] = useState('performance');
  const { signals } = useHighPerformingSignals();
  const correlations = useMarketCorrelations();
  
  return (
    <div className="space-y-6">
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setTab('performance')}
          className={`px-4 py-2 ${tab === 'performance' ? 'border-b-2 border-blue-500' : ''}`}
        >
          Signal Performance
        </button>
        <button
          onClick={() => setTab('sources')}
          className={`px-4 py-2 ${tab === 'sources' ? 'border-b-2 border-blue-500' : ''}`}
        >
          External Sources
        </button>
        <button
          onClick={() => setTab('correlations')}
          className={`px-4 py-2 ${tab === 'correlations' ? 'border-b-2 border-blue-500' : ''}`}
        >
          Market Correlations
        </button>
      </div>
      
      {tab === 'performance' && (
        <HighPerformancePanel signals={signals} />
      )}
      
      {tab === 'sources' && (
        <ExternalSignalSourcesList />
      )}
      
      {tab === 'correlations' && (
        <CorrelationHeatmap data={correlations} />
      )}
    </div>
  );
}
```

## 🔐 Authentication

All endpoints require Firebase authentication token:

```typescript
import { getAuth } from 'firebase/auth';

async function getAuthToken() {
  const auth = getAuth();
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  throw new Error('User not authenticated');
}

// Use in headers
const headers = {
  'Authorization': `Bearer ${await getAuthToken()}`,
  'Content-Type': 'application/json'
};
```

## 📱 Usage Patterns

### Real-time Performance Updates
```typescript
// Poll every 10s for updates
useEffect(() => {
  const interval = setInterval(() => {
    fetchHighPerformers();
  }, 10000);
  
  return () => clearInterval(interval);
}, []);
```

### WebSocket for Live Data
```typescript
// Monitor real-time ticker correlations
async function subscribeToCorrelations() {
  const response = await fetch('/api/websocket/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { status } = await response.json();
  
  if (status.connected) {
    // Subscribe to correlation updates
    console.log('Connected to', status.subscribed_channels);
  }
}
```

## 🚀 Deployment Considerations

1. **Rate Limiting**: These endpoints may be called frequently - consider implementing rate limiting on frontend
2. **Caching**: Cache recommendations for 30-60 seconds to reduce backend load
3. **Error Handling**: Implement fallbacks when services are unavailable
4. **Performance**: Monitor response times and log slow endpoints
5. **Authentication**: Ensure tokens are refreshed before expiration

## 📈 Metrics to Track

- Signal win rate trends
- External source reliability changes
- Correlation matrix stability
- Cache hit rates
- WebSocket connection health
