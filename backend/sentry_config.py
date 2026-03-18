"""
Sentry configuration for error tracking and monitoring.
Place this in backend/sentry_config.py
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
import logging

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry SDK for error tracking.
    
    Usage in backend/main.py:
        from sentry_config import init_sentry
        init_sentry()
    
    Environment variables:
        SENTRY_DSN: Sentry project DSN
        SENTRY_ENVIRONMENT: Environment name (development, staging, production)
        SENTRY_SAMPLE_RATE: Traces sample rate (0.0 - 1.0, default 0.1 for production, 1.0 for dev)
        SENTRY_RELEASE: Release version (optional, auto-detected from git if available)
    """
    
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("SENTRY_DSN not set, Sentry will not be initialized")
        return
    
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    sample_rate = float(os.getenv("SENTRY_SAMPLE_RATE", "1.0" if environment == "development" else "0.1"))
    release = os.getenv("SENTRY_RELEASE")
    
    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,           # Capture info and above as breadcrumbs
        event_level=logging.ERROR,     # Send ERROR and above as events
    )
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=sample_rate,
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            release=release,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
                SqlAlchemyIntegration(),
                sentry_logging,
            ],
            # Performance monitoring
            enable_tracing=True,
            # Send server name for production
            server_name=os.getenv("SERVER_NAME"),
            # Custom before_send to filter sensitive data
            before_send=_before_send,
        )
        logger.info(f"Sentry initialized: environment={environment}, sample_rate={sample_rate}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _before_send(event, hint):
    """
    Filter events before sending to Sentry.
    Remove sensitive information like API keys, passwords, etc.
    """
    
    # Remove sensitive headers
    if "request" in event and "headers" in event.get("request", {}):
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "x-api-key", "cookie", "password"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"
    
    # Remove sensitive request body data
    if "request" in event and "data" in event.get("request", {}):
        try:
            import json
            data = json.loads(event["request"]["data"]) if isinstance(event["request"]["data"], str) else event["request"]["data"]
            _redact_dict(data)
            event["request"]["data"] = data
        except Exception:
            pass
    
    # Remove sensitive exception data
    if "exception" in event:
        for exception in event.get("exception", {}).get("values", []):
            if "value" in exception:
                # Redact any email addresses or API keys in error messages
                exception["value"] = _redact_string(exception["value"])
    
    return event


def _redact_dict(data):
    """Recursively redact sensitive keys in a dictionary."""
    sensitive_keys = [
        "password", "token", "api_key", "secret", "auth",
        "email", "phone", "ssn", "credit_card"
    ]
    
    for key, value in data.items():
        key_lower = key.lower()
        
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            data[key] = "[REDACTED]"
        elif isinstance(value, dict):
            _redact_dict(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for item in value:
                if isinstance(item, dict):
                    _redact_dict(item)


def _redact_string(s):
    """Redact sensitive information from strings."""
    if not isinstance(s, str):
        return s
    
    import re
    
    # Redact email addresses
    s = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', s)
    
    # Redact API keys (common patterns)
    s = re.sub(r'(?:api[_-]?key|Bearer\s+)[^\s]+', '[API_KEY]', s, flags=re.IGNORECASE)
    
    # Redact tokens
    s = re.sub(r'(?:token|jwt)[^\s]*', '[TOKEN]', s, flags=re.IGNORECASE)
    
    return s


def capture_exception(exception, context: dict = None):
    """
    Capture an exception with optional context.
    
    Usage:
        try:
            # some code
        except Exception as e:
            capture_exception(e, {"user_id": user_id, "trade_id": trade_id})
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, {"value": value})
            sentry_sdk.capture_exception(exception)
    else:
        sentry_sdk.capture_exception(exception)


def capture_message(message, level="info", context: dict = None):
    """
    Capture a message for monitoring.
    
    Usage:
        capture_message("Trade executed successfully", "info", {"trade_id": "123"})
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, {"value": value})
            sentry_sdk.capture_message(message, level)
    else:
        sentry_sdk.capture_message(message, level)
