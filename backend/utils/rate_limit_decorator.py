"""
Rate limiting decorator for FastAPI endpoints.
"""

import time
from typing import Callable, Dict
from functools import wraps
from fastapi import HTTPException


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests: Dict[str, list] = {}

    def is_allowed(self, key: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit.

        Args:
            key: Identifier for rate limiting (e.g., IP address, user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()
        cutoff = now - window_seconds

        if key not in self.requests:
            self.requests[key] = []

        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        if len(self.requests[key]) >= max_requests:
            return False

        self.requests[key].append(now)
        return True


_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 5, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints.

    Usage:
        @app.post("/api/auth/login")
        @rate_limit(max_requests=5, window_seconds=60)
        async def login(credentials):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import Request

            for arg in args:
                if isinstance(arg, Request):
                    client_ip = arg.client.host if request.client else "unknown"
                    if not _rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
                        )
                    break

            return await func(*args, **kwargs)

        return wrapper

    return decorator
