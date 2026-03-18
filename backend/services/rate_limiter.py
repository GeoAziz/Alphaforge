"""
API Rate Limiting & Throttling
Implements per-user and per-endpoint rate limiting to prevent abuse
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API endpoints"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_minute / 60
        # User ID -> {timestamp: last_request, tokens: available_tokens}
        self.users: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": self.requests_per_minute,
            "last_refill": datetime.utcnow()
        })
        self.endpoint_limits: Dict[str, int] = {
            "/api/signals/high-performers": 30,  # 30 req/min
            "/api/external-signals/sources": 20,  # 20 req/min
            "/api/market/correlations": 15,      # 15 req/min
            "/api/market/signals/conflicts": 10,  # 10 req/min (expensive)
            "/api/cache/stats": 60,              # 60 req/min
            "/api/websocket/status": 60,         # 60 req/min
        }
    
    def _refill_tokens(self, user_id: str) -> float:
        """Refill tokens based on time elapsed"""
        user = self.users[user_id]
        now = datetime.utcnow()
        time_passed = (now - user["last_refill"]).total_seconds()
        
        # Add tokens based on time passed
        tokens_to_add = time_passed * self.requests_per_second
        user["tokens"] = min(
            self.requests_per_minute,
            user["tokens"] + tokens_to_add
        )
        user["last_refill"] = now
        
        return user["tokens"]
    
    def is_allowed(self, user_id: str, endpoint: str = "/") -> Tuple[bool, Dict]:
        """Check if request is allowed and return rate limit info"""
        # Get endpoint-specific limit
        limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
        
        # Refill tokens
        tokens = self._refill_tokens(user_id)
        
        # Check if allowed
        if tokens >= 1:
            self.users[user_id]["tokens"] = tokens - 1
            logger.debug(f"✅ Rate limit OK for {user_id}: {tokens - 1:.1f} tokens remaining")
            return True, {
                "limit": limit,
                "remaining": int(tokens - 1),
                "reset_seconds": 60
            }
        else:
            retry_after = (1 - tokens) / self.requests_per_second
            logger.warning(f"⚠️ Rate limit exceeded for {user_id} on {endpoint}")
            return False, {
                "limit": limit,
                "remaining": 0,
                "retry_after_seconds": int(retry_after) + 1
            }
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get current rate limit stats for user"""
        user = self.users.get(user_id, {})
        return {
            "user_id": user_id,
            "available_tokens": user.get("tokens", 0),
            "requests_per_minute": self.requests_per_minute,
            "last_request": user.get("last_refill", "Never").isoformat() if isinstance(user.get("last_refill"), datetime) else "Never"
        }


class AdaptiveRateLimiter(RateLimiter):
    """Adaptive rate limiter that adjusts limits based on system load"""
    
    def __init__(self, base_requests_per_minute: int = 60):
        super().__init__(base_requests_per_minute)
        self.request_count_window = defaultdict(int)  # endpoint -> count in last minute
        self.error_count_window = defaultdict(int)     # endpoint -> error count in last minute
        self.window_start = datetime.utcnow()
    
    def record_request(self, endpoint: str, success: bool):
        """Record a request for statistics"""
        now = datetime.utcnow()
        
        # Reset window if minute has passed
        if (now - self.window_start).total_seconds() > 60:
            self.request_count_window.clear()
            self.error_count_window.clear()
            self.window_start = now
        
        self.request_count_window[endpoint] += 1
        if not success:
            self.error_count_window[endpoint] += 1
    
    def get_adaptive_limit(self, endpoint: str) -> int:
        """Get adjusted limit based on error rate"""
        total_requests = self.request_count_window.get(endpoint, 0)
        total_errors = self.error_count_window.get(endpoint, 0)
        
        if total_requests == 0:
            return self.endpoint_limits.get(endpoint, self.requests_per_minute)
        
        error_rate = total_errors / total_requests
        base_limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
        
        # Reduce limit if error rate is high
        if error_rate > 0.1:  # >10% errors
            adjusted_limit = int(base_limit * 0.5)
            logger.warning(f"⚠️ High error rate ({error_rate:.1%}) on {endpoint}, reducing limit to {adjusted_limit}")
            return adjusted_limit
        elif error_rate > 0.05:
            return int(base_limit * 0.75)
        
        return base_limit
    
    def is_allowed(self, user_id: str, endpoint: str = "/") -> Tuple[bool, Dict]:
        """Check with adaptive limits"""
        adaptive_limit = self.get_adaptive_limit(endpoint)
        
        # Refill tokens based on adaptive limit
        user = self.users[user_id]
        now = datetime.utcnow()
        time_passed = (now - user["last_refill"]).total_seconds()
        adaptive_rate = adaptive_limit / 60
        
        tokens_to_add = time_passed * adaptive_rate
        user["tokens"] = min(adaptive_limit, user["tokens"] + tokens_to_add)
        user["last_refill"] = now
        
        if user["tokens"] >= 1:
            user["tokens"] -= 1
            return True, {
                "limit": adaptive_limit,
                "remaining": int(user["tokens"]),
                "reset_seconds": 60
            }
        else:
            retry_after = (1 - user["tokens"]) / adaptive_rate
            return False, {
                "limit": adaptive_limit,
                "remaining": 0,
                "retry_after_seconds": int(retry_after) + 1
            }


class RateLimitingMiddleware:
    """ASGI middleware for rate limiting"""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        self.app = app
        self.rate_limiter = rate_limiter or AdaptiveRateLimiter()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get user ID from headers or use IP
        headers = dict(scope.get("headers", []))
        user_id = headers.get(b"x-user-id", headers.get(b"authorization", b"anonymous")).decode()[:50]
        
        path = scope.get("path", "/")
        
        # Check rate limit
        allowed, rate_info = self.rate_limiter.is_allowed(user_id, path)
        
        if not allowed:
            # Send 429 Too Many Requests
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"retry-after", str(rate_info["retry_after_seconds"]).encode()],
                    [b"x-ratelimit-limit", str(rate_info["limit"]).encode()],
                    [b"x-ratelimit-remaining", b"0"],
                ],
            })
            
            await send({
                "type": "http.response.body",
                "body": f'{{"error": "Rate limit exceeded", "retry_after_seconds": {rate_info["retry_after_seconds"]}}}'.encode(),
            })
            return
        
        # Add rate limit headers to response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    [b"x-ratelimit-limit", str(rate_info["limit"]).encode()],
                    [b"x-ratelimit-remaining", str(rate_info["remaining"]).encode()],
                    [b"x-ratelimit-reset", str(60).encode()],
                ])
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdaptiveRateLimiter()
    return _rate_limiter
