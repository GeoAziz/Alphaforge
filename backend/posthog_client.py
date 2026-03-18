"""
PostHog analytics integration for backend event tracking.
Place this in backend/posthog_client.py
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global PostHog instance
_posthog_client = None


class PostHogClientWrapper:
    """
    Wrapper around PostHog client for event tracking.
    
    Usage:
        from posthog_client import get_posthog_client
        
        ph = get_posthog_client()
        ph.track(
            user_id="user123",
            event="trade_executed",
            properties={"asset": "BTC", "quantity": 1.5}
        )
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        
        api_key = os.getenv("POSTHOG_API_KEY")
        if not api_key:
            logger.warning("POSTHOG_API_KEY not set, PostHog analytics disabled")
            return
        
        try:
            from posthog import Posthog
            
            host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
            self.client = Posthog(
                api_key=api_key,
                host=host,
            )
            self.enabled = True
            logger.info(f"PostHog initialized: {host}")
            
        except ImportError:
            logger.warning("posthog package not installed. Run: pip install posthog")
        except Exception as e:
            logger.error(f"Failed to initialize PostHog: {e}")
    
    def track(
        self,
        user_id: str,
        event: str,
        properties: Dict[str, Any] = None,
    ) -> None:
        """
        Track an event for a user.
        
        Args:
            user_id: Unique user identifier
            event: Event name
            properties: Optional properties/context
        """
        if not self.enabled or not self.client:
            return
        
        try:
            properties = properties or {}
            properties["timestamp"] = datetime.utcnow().isoformat()
            
            self.client.capture(
                distinct_id=user_id,
                event=event,
                properties=properties,
            )
            
            logger.debug(f"Tracked: {event} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to track event: {e}", exc_info=True)
    
    def identify(
        self,
        user_id: str,
        properties: Dict[str, Any] = None,
    ) -> None:
        """
        Identify a user with properties.
        
        Args:
            user_id: Unique user identifier
            properties: User properties (email, name, plan, etc.)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            properties = properties or {}
            
            self.client.identify(
                distinct_id=user_id,
                properties=properties,
            )
            
            logger.debug(f"Identified user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to identify user: {e}", exc_info=True)
    
    def group_identify(
        self,
        group_type: str,
        group_id: str,
        properties: Dict[str, Any] = None,
    ) -> None:
        """
        Set properties for a group (organization, team, etc.).
        
        Args:
            group_type: Type of group (e.g., "organization")
            group_id: Unique group identifier
            properties: Group properties
        """
        if not self.enabled or not self.client:
            return
        
        try:
            properties = properties or {}
            
            self.client.group_identify(
                group_type=group_type,
                group_key=group_id,
                properties=properties,
            )
            
            logger.debug(f"Identified group: {group_type}/{group_id}")
            
        except Exception as e:
            logger.error(f"Failed to identify group: {e}", exc_info=True)
    
    def group_track(
        self,
        user_id: str,
        group_type: str,
        group_id: str,
        event: str,
        properties: Dict[str, Any] = None,
    ) -> None:
        """
        Track event with group context.
        
        Args:
            user_id: User identifier
            group_type: Type of group
            group_id: Group identifier
            event: Event name
            properties: Event properties
        """
        if not self.enabled or not self.client:
            return
        
        try:
            properties = properties or {}
            properties["timestamp"] = datetime.utcnow().isoformat()
            
            self.client.capture(
                distinct_id=user_id,
                event=event,
                properties=properties,
                groups={group_type: group_id},
            )
            
            logger.debug(f"Tracked: {event} for user {user_id} in {group_type}/{group_id}")
            
        except Exception as e:
            logger.error(f"Failed to track group event: {e}", exc_info=True)
    
    def flush(self) -> None:
        """Flush pending events."""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush events: {e}")


def get_posthog_client() -> PostHogClientWrapper:
    """Get or create PostHog client instance."""
    global _posthog_client
    if _posthog_client is None:
        _posthog_client = PostHogClientWrapper()
    return _posthog_client


# Event tracking utility functions

def track_user_signup(user_id: str, email: str, plan: str = "free"):
    """Track user signup event."""
    get_posthog_client().track(
        user_id=user_id,
        event="user_signup",
        properties={"email": email, "plan": plan},
    )


def track_user_login(user_id: str):
    """Track user login event."""
    get_posthog_client().track(
        user_id=user_id,
        event="user_login",
    )


def track_trade_executed(
    user_id: str,
    trade_type: str,
    asset: str,
    quantity: float,
    price: Optional[float] = None,
    exchange: str = "paper",
):
    """Track trade execution event."""
    get_posthog_client().track(
        user_id=user_id,
        event="trade_executed",
        properties={
            "trade_type": trade_type,
            "asset": asset,
            "quantity": quantity,
            "price": price,
            "exchange": exchange,
        },
    )


def track_strategy_subscribed(user_id: str, strategy_id: str, strategy_name: str):
    """Track strategy subscription event."""
    get_posthog_client().track(
        user_id=user_id,
        event="strategy_subscribed",
        properties={"strategy_id": strategy_id, "strategy_name": strategy_name},
    )


def track_signal_received(user_id: str, signal_type: str, confidence: float):
    """Track signal received event."""
    get_posthog_client().track(
        user_id=user_id,
        event="signal_received",
        properties={"signal_type": signal_type, "confidence": confidence},
    )


def track_backtest_run(user_id: str, strategy_id: str, duration_days: int):
    """Track backtest execution."""
    get_posthog_client().track(
        user_id=user_id,
        event="backtest_run",
        properties={"strategy_id": strategy_id, "duration_days": duration_days},
    )


def track_api_error(
    user_id: Optional[str],
    endpoint: str,
    status_code: int,
    error_type: str,
):
    """Track API errors."""
    get_posthog_client().track(
        user_id=user_id or "anonymous",
        event="api_error",
        properties={
            "endpoint": endpoint,
            "status_code": status_code,
            "error_type": error_type,
        },
    )
