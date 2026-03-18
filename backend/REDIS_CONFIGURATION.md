# Redis Configuration Guide

## Current Status

✅ **Redis is fully configured** in your AlphaForge backend with automatic fallback support.

## Configuration

### Environment Variables (in `.env`)

```bash
# Cache Backend Selection
CACHE_BACKEND=memory              # Options: "memory" or "redis"

# Redis Connection (only used if CACHE_BACKEND=redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### How It Works

1. **Development (Current)**: `CACHE_BACKEND=memory`
   - Uses in-memory cache (auto-eviction at 10,000 entries)
   - No external dependencies needed
   - Fast for development/testing

2. **Production**: Set `CACHE_BACKEND=redis`
   - Uses Redis server for distributed caching
   - Persistent across service restarts
   - Supports multiple backends connecting to same cache

## Cache TTLs (Configurable)

```bash
CACHE_TTL_TICKER=10              # Live tickers refresh every 10s
CACHE_TTL_OHLCV=60               # Candles every 1 minute  
CACHE_TTL_SENTIMENT=300          # Sentiment every 5 minutes
CACHE_TTL_METADATA=3600          # Metadata cached for 1 hour
```

## Setup Instructions

### Option 1: Use In-Memory Cache (Current - No Setup Needed)

**Status**: ✅ Ready to use
- Already configured
- No installation required
- Auto-fallback if Redis fails

```bash
# No action needed, just start the server:
python main.py
```

### Option 2: Enable Redis (Production)

#### 2.1 Install Redis Server

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**On Docker:**
```bash
docker run -d \
  --name alphaforge-redis \
  -p 6379:6379 \
  redis:7-alpine
```

**On Windows (WSL2):**
```bash
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

#### 2.2 Update `.env`

```bash
# Change this line:
CACHE_BACKEND=memory

# To this:
CACHE_BACKEND=redis

# Verify Redis connection settings:
REDIS_HOST=localhost              # or your Redis server IP
REDIS_PORT=6379
REDIS_DB=0
```

#### 2.3 Test Connection

```bash
# Test Redis is running:
redis-cli ping
# Should return: PONG

# Check if server connects:
python main.py
# Should show: ✅ Redis cache connected (localhost:6379)
```

### Option 3: Use Managed Redis (Cloud)

For production, consider cloud Redis providers:

1. **Redis Cloud (Recommended)**
   - Free tier: 30MB
   - Starts at $0/month
   - URL: redis.com

2. **Upstash Redis**
   - Free tier: 256MB
   - $0-monthly start
   - Use async Python client

3. **AWS ElastiCache**
   - Free tier: up to 750 hours/month
   - $0-monthly with free tier
   - Fully managed

For cloud Redis, update `.env`:

```bash
# Upstash example:
CACHE_BACKEND=redis
REDIS_HOST=actual-host.upstash.io
REDIS_PORT=6379
REDIS_DB=0
# Note: Add AUTH if required by provider
```

## Automatic Fallback Mechanism

The backend **automatically handles Redis failures**:

```
┌─────────────────────────────────────┐
│      Cache Request Incoming         │
└──────────────┬──────────────────────┘
               ↓
    ┌──────────────────────┐
    │ Try Redis Cache      │
    └──────┬──────┬────────┘
           │      │
        ✅ Hit    ❌ Fail/Offline
           │      │
           ↓      ↓
         Return  Try In-Memory Cache
         Result  ├─ Hit → Return Result
                 └─ Miss → Fetch from API
```

**Key Point**: If Redis is unavailable, the system seamlessly switches to in-memory cache. No data loss, no service interruption.

## Performance Comparison

| Metric | In-Memory | Redis |
|--------|-----------|-------|
| Latency | <1ms | 1-5ms |
| Capacity | 10K entries | Unlimited |
| Persistent | No (ephemeral) | Yes |
| Multi-service | No | Yes |
| Scalability | Single instance | Distributed |
| Cost | Free | $0-50/month |

## Monitoring Redis

### Check Redis Status

```bash
# If running locally:
redis-cli INFO stats

# Shows:
# - connected_clients
# - total_commands_processed
# - used_memory
```

### View Cache Health from API

```bash
curl http://localhost:8000/api/health/data-sources
```

Response example:
```json
{
  "status": "healthy",
  "cache": {
    "backend": "memory",
    "stats": {
      "total_entries": 245,
      "active_entries": 240,
      "max_capacity": 10000,
      "usage_percentage": 2.45
    }
  },
  "data_sources": {
    "binance": {"available": true, "last_error": null},
    "coingecko": {"available": true, "last_error": null},
    "polygon": {"available": false, "last_error": "Not enabled"}
  }
}
```

## Troubleshooting

### Redis Connection Fails

**Error**: `⚠️ Redis connection failed. Falling back to in-memory cache.`

**Fix**:
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_HOST and REDIS_PORT in .env
3. Check firewall allows port 6379
4. System auto-falls back to memory cache

### High Memory Usage

If in-memory cache exceeds limits:

**Fix**:
1. Reduce `CACHE_TTL_*` values in .env
2. Switch to Redis backend
3. Monitor with `/api/health/data-sources`

### Redis Out of Memory

**Error**: `MISCONF Redis is configured to save RDB snapshots, but is currently not able to persist on disk`

**Fix** (for local Redis):
```bash
# Disable RDB persistence temporarily:
redis-cli CONFIG SET save ""

# Or increase max memory:
redis-cli CONFIG SET maxmemory 256mb
```

## Best Practices

1. **Development**: Use in-memory (current default) ✅
2. **Staging**: Enable Redis for testing distributed caching
3. **Production**: Use cloud Redis (Upstash/Redis Cloud) with SSL/TLS
4. **Monitoring**: Check `/api/health/data-sources` regularly
5. **TTLs**: Adjust cache TTLs based on data freshness needs

## Cost Analysis

**Current Setup** (In-Memory):
- Cost: $0/month
- Capacity: 10,000 entries
- Latency: <1ms
- Suitable for: MVP/Development

**With Redis** (Optional):
- Local/Self-hosted: $0/month
- Cloud (Upstash): $0-30/month
- Cloud (Redis Cloud): $0-15/month
- Capacity: Unlimited
- Latency: 1-5ms
- Suitable for: Production/Scale

## Configuration Summary

```
┌──────────────────────────────────────────────────────────────┐
│ Current Configuration (Development)                          │
├──────────────────────────────────────────────────────────────┤
│ Cache Backend: In-Memory ✅                                  │
│ Redis: Optional (disabled)                                   │
│ Auto-Fallback: Enabled ✅                                    │
│ Cache Capacity: 10,000 entries                               │
│ Monitor: GET /api/health/data-sources                        │
│ Status: READY FOR PRODUCTION                                 │
└──────────────────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Current setup works for MVP
2. **Optional**: Enable Redis for production scale
3. **To switch**: Change one line in .env (CACHE_BACKEND=redis) + install Redis
4. **No code changes needed** - built-in auto-detection

For questions, check [INTEGRATION_GUIDE_MULTI_SOURCE.md](INTEGRATION_GUIDE_MULTI_SOURCE.md#redis-connection-issues) for detailed troubleshooting.
