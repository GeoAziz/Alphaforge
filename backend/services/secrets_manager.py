"""
Production Secrets Management
Integration with AWS Secrets Manager for secure credential handling.
"""

import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class SecretsManager:
    """AWS Secrets Manager integration for AlphaForge."""

    def __init__(
        self,
        region: str = "us-east-1",
        cache_ttl: int = 300,
    ):
        self.region = region
        self.cache_ttl = cache_ttl
        self._client = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    async def initialize(self) -> bool:
        """Initialize Secrets Manager client."""
        if not BOTO3_AVAILABLE:
            logger.warning("boto3 not installed. Secrets Manager disabled.")
            return False

        try:
            self._client = boto3.client("secretsmanager", region_name=self.region)
            logger.info(f"✅ Secrets Manager initialized (region: {self.region})")
            return True
        except Exception as e:
            logger.error(f"❌ Secrets Manager initialization failed: {e}")
            return False

    # ==========================================================================
    # Secret Operations
    # ==========================================================================

    def get_secret(self, secret_id: str) -> Optional[Dict[str, Any]]:
        """Get a secret value (with caching)."""
        # Check cache first
        with self._lock:
            if secret_id in self._cache:
                cached = self._cache[secret_id]
                if time.time() - cached["fetched_at"] < self.cache_ttl:
                    return cached["value"]

        # Fetch from Secrets Manager
        if not self._client:
            logger.warning(f"Secrets Manager not available, trying env var: {secret_id}")
            env_value = os.getenv(secret_id)
            if env_value:
                try:
                    return json.loads(env_value)
                except json.JSONDecodeError:
                    return {"value": env_value}
            return None

        try:
            response = self._client.get_secret_value(SecretId=secret_id)
            secret_string = response["SecretString"]
            secret_value = json.loads(secret_string)

            # Update cache
            with self._lock:
                self._cache[secret_id] = {
                    "value": secret_value,
                    "fetched_at": time.time(),
                }

            return secret_value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret not found: {secret_id}")
            else:
                logger.error(f"Failed to get secret {secret_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting secret {secret_id}: {e}")
            return None

    def get_secret_value(self, secret_id: str, key: Optional[str] = None) -> Optional[str]:
        """Get a specific value from a secret."""
        secret = self.get_secret(secret_id)
        if secret is None:
            return None

        if key and isinstance(secret, dict):
            return secret.get(key)

        if isinstance(secret, dict) and "value" in secret:
            return secret["value"]

        return str(secret) if secret else None

    def put_secret(self, secret_id: str, value: Dict[str, Any]) -> bool:
        """Create or update a secret."""
        if not self._client:
            logger.warning("Secrets Manager not available")
            return False

        try:
            secret_string = json.dumps(value, default=str)

            # Try to update existing secret
            try:
                self._client.update_secret(
                    SecretId=secret_id,
                    SecretString=secret_string,
                )
                logger.info(f"✅ Secret updated: {secret_id}")
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Create new secret
                    self._client.create_secret(
                        Name=secret_id,
                        SecretString=secret_string,
                    )
                    logger.info(f"✅ Secret created: {secret_id}")
                    return True
                raise

        except Exception as e:
            logger.error(f"Failed to put secret {secret_id}: {e}")
            return False

    def rotate_secret(self, secret_id: str, new_value: Dict[str, Any]) -> bool:
        """Rotate a secret value."""
        success = self.put_secret(secret_id, new_value)
        if success:
            # Clear cache
            with self._lock:
                self._cache.pop(secret_id, None)
            logger.info(f"✅ Secret rotated: {secret_id}")
        return success

    # ==========================================================================
    # Bulk Operations
    # ==========================================================================

    def load_all_secrets(self, prefix: str = "alphaforge/") -> Dict[str, Any]:
        """Load all secrets with a given prefix."""
        if not self._client:
            return {}

        secrets = {}
        try:
            paginator = self._client.get_paginator("list_secrets")
            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    name = secret["Name"]
                    if name.startswith(prefix):
                        short_name = name[len(prefix):]
                        value = self.get_secret(name)
                        if value:
                            secrets[short_name] = value

            logger.info(f"✅ Loaded {len(secrets)} secrets with prefix '{prefix}'")
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")

        return secrets

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check Secrets Manager health."""
        if not self._client:
            return {"status": "disconnected", "backend": "env_vars"}

        try:
            # Try to list secrets (minimal permission check)
            self._client.list_secrets(MaxResults=1)
            return {
                "status": "healthy",
                "backend": "aws_secrets_manager",
                "cached_secrets": len(self._cache),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "aws_secrets_manager",
                "error": str(e),
            }


# Global instance
secrets_manager: Optional[SecretsManager] = None


async def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager."""
    global secrets_manager
    if secrets_manager is None:
        secrets_manager = SecretsManager(
            region=os.getenv("AWS_REGION", "us-east-1"),
        )
        await secrets_manager.initialize()
    return secrets_manager
