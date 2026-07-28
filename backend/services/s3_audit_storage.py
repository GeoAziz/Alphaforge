"""
S3 Audit Storage Service
Immutable audit trail storage with hash chaining for regulatory compliance.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed. S3 audit storage disabled.")


class S3AuditStorage:
    """Immutable audit storage in S3 with hash chaining."""

    def __init__(
        self,
        bucket: str = "alphaforge-audit",
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self._client = None
        self._last_hash: Optional[str] = None

    async def initialize(self) -> bool:
        """Initialize S3 client."""
        if not BOTO3_AVAILABLE:
            logger.warning("S3 not available (boto3 not installed)")
            return False

        try:
            kwargs = {"region_name": self.region}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client("s3", **kwargs)

            # Ensure bucket exists
            try:
                self._client.head_bucket(Bucket=self.bucket)
                logger.info(f"✅ S3 bucket exists: {self.bucket}")
            except ClientError:
                self._client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration={"LocationConstraint": self.region},
                )
                logger.info(f"✅ S3 bucket created: {self.bucket}")

            # Enable versioning for immutability
            try:
                self._client.put_bucket_versioning(
                    Bucket=self.bucket,
                    VersioningConfiguration={"Status": "Enabled"},
                )
            except Exception as e:
                logger.warning(f"Failed to enable versioning: {e}")

            return True
        except Exception as e:
            logger.error(f"❌ S3 initialization failed: {e}")
            return False

    # ==========================================================================
    # Hash Chain Utilities
    # ==========================================================================

    def _compute_hash(self, data: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
        """Compute SHA-256 hash of audit entry."""
        hash_input = json.dumps(data, sort_keys=True, default=str)
        if prev_hash:
            hash_input = prev_hash + hash_input
        return hashlib.sha256(hash_input.encode()).hexdigest()

    # ==========================================================================
    # Audit Logging
    # ==========================================================================

    async def store_audit_entry(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_id: str,
        new_value: Dict[str, Any],
        old_value: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store an immutable audit entry in S3."""
        if not self._client:
            logger.warning("S3 not available, audit entry dropped")
            return ""

        try:
            # Compute hash chain
            entry_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "actor_id": actor_id,
                "old_value": old_value,
                "new_value": new_value,
                "timestamp": datetime.utcnow().isoformat(),
            }
            entry_hash = self._compute_hash(entry_data, self._last_hash)

            audit_record = {
                **entry_data,
                "hash": entry_hash,
                "prev_hash": self._last_hash or "",
            }

            # Update chain
            self._last_hash = entry_hash

            # Determine S3 key
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            hour_str = datetime.utcnow().strftime("%H")
            key = f"audit-logs/{date_str}/{hour_str}/{entity_type}_{entity_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

            # Upload with server-side encryption
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(audit_record, default=str),
                ContentType="application/json",
                ServerSideEncryption="AES256",
                Metadata={
                    "entity-type": entity_type,
                    "entity-id": entity_id,
                    "action": action,
                    "hash": entry_hash,
                },
            )

            logger.debug(f"✅ Audit entry stored: {key}")
            return key

        except Exception as e:
            logger.error(f"❌ Failed to store audit entry: {e}")
            return ""

    # ==========================================================================
    # Audit Retrieval
    # ==========================================================================

    async def get_audit_entries(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit entries from S3."""
        if not self._client:
            return []

        try:
            prefix = "audit-logs/"
            if start_date:
                prefix = f"audit-logs/{start_date.strftime('%Y-%m-%d')}/"

            entries = []
            paginator = self._client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if len(entries) >= limit:
                        break

                    try:
                        response = self._client.get_object(
                            Bucket=self.bucket, Key=obj["Key"]
                        )
                        content = json.loads(response["Body"].read().decode())

                        # Filter by entity type/id if specified
                        if entity_type and content.get("entity_type") != entity_type:
                            continue
                        if entity_id and content.get("entity_id") != entity_id:
                            continue

                        entries.append(content)
                    except Exception:
                        continue

            return entries[:limit]

        except Exception as e:
            logger.error(f"Failed to retrieve audit entries: {e}")
            return []

    # ==========================================================================
    # Backup Support
    # ==========================================================================

    async def store_backup(
        self,
        backup_type: str,
        data: bytes,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Store a backup file in S3."""
        if not self._client:
            return ""

        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"backups/{backup_type}/{date_str}/{backup_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.dump"

            put_kwargs = {
                "Bucket": self.bucket,
                "Key": key,
                "Body": data,
                "ServerSideEncryption": "AES256",
                "StorageClass": "STANDARD_IA",
            }
            if metadata:
                put_kwargs["Metadata"] = metadata

            self._client.put_object(**put_kwargs)
            logger.info(f"✅ Backup stored: {key}")
            return key

        except Exception as e:
            logger.error(f"Failed to store backup: {e}")
            return ""

    async def store_model(
        self,
        model_name: str,
        version: str,
        model_data: bytes,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Store an ML model in S3."""
        if not self._client:
            return ""

        try:
            key = f"models/{model_name}/{version}/model.pkl"

            put_kwargs = {
                "Bucket": self.bucket,
                "Key": key,
                "Body": model_data,
                "ServerSideEncryption": "AES256",
            }
            if metadata:
                put_kwargs["Metadata"] = metadata

            self._client.put_object(**put_kwargs)

            # Also store metadata JSON
            meta_key = f"models/{model_name}/{version}/metadata.json"
            self._client.put_object(
                Bucket=self.bucket,
                Key=meta_key,
                Body=json.dumps(metadata or {}, default=str),
                ContentType="application/json",
            )

            logger.info(f"✅ Model stored: {key}")
            return key

        except Exception as e:
            logger.error(f"Failed to store model: {e}")
            return ""

    # ==========================================================================
    # Verification
    # ==========================================================================

    async def verify_audit_chain(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify the hash chain integrity of audit entries."""
        if not entries:
            return {"valid": True, "entries_verified": 0}

        valid_count = 0
        broken_at = None

        for i, entry in enumerate(entries):
            if i == 0:
                if entry.get("prev_hash", "") == "":
                    valid_count += 1
                    continue
                else:
                    broken_at = i
                    break

            expected_prev = entries[i - 1].get("hash", "")
            actual_prev = entry.get("prev_hash", "")

            if expected_prev == actual_prev:
                valid_count += 1
            else:
                broken_at = i
                break

        return {
            "valid": broken_at is None,
            "entries_verified": valid_count,
            "total_entries": len(entries),
            "broken_at_index": broken_at,
        }

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check S3 health."""
        if not self._client:
            return {"status": "disconnected", "backend": "s3"}

        try:
            self._client.head_bucket(Bucket=self.bucket)
            return {
                "status": "healthy",
                "backend": "s3",
                "bucket": self.bucket,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "s3",
                "error": str(e),
            }


# Global instance
s3_audit_storage: Optional[S3AuditStorage] = None


async def get_s3_audit_storage() -> S3AuditStorage:
    """Get or create the global S3 audit storage."""
    global s3_audit_storage
    if s3_audit_storage is None:
        s3_audit_storage = S3AuditStorage(
            bucket=os.getenv("S3_AUDIT_BUCKET", "alphaforge-audit"),
            region=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        )
        await s3_audit_storage.initialize()
    return s3_audit_storage
