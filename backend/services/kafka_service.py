"""
Kafka Message Streaming Service
Handles event production and consumption for AlphaForge's event-driven architecture.
"""

import json
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError, KafkaTimeoutError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed. Kafka features disabled.")


class KafkaService:
    """Kafka producer and consumer for AlphaForge events."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "alphaforge",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self._producer: Optional[KafkaProducer] = None
        self._consumers: Dict[str, KafkaConsumer] = {}
        self._running = False
        self._topics = {
            "market-prices": {"partitions": 10, "retention_ms": 3600000},
            "signals-generated": {"partitions": 20, "retention_ms": 86400000},
            "executions": {"partitions": 20, "retention_ms": 86400000},
            "positions-updated": {"partitions": 10, "retention_ms": 86400000},
            "kyc-events": {"partitions": 5, "retention_ms": 2592000000},
            "marketplace-events": {"partitions": 5, "retention_ms": 604800000},
            "audit-events": {"partitions": 5, "retention_ms": 7776000000},
        }

    async def initialize(self) -> bool:
        """Initialize Kafka producer."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available, using in-memory fallback")
            return False

        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
                compression_type="snappy",
                linger_ms=10,
                batch_size=32768,
            )
            self._running = True
            logger.info(f"✅ Kafka producer initialized: {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka producer initialization failed: {e}")
            return False

    async def close(self):
        """Close Kafka connections."""
        self._running = False
        if self._producer:
            self._producer.flush(timeout=10)
            self._producer.close(timeout=10)
            logger.info("🔌 Kafka producer closed")

        for topic, consumer in self._consumers.items():
            try:
                consumer.close()
            except Exception:
                pass
        self._consumers.clear()

    # ==========================================================================
    # Producer Methods
    # ==========================================================================

    async def publish(
        self,
        topic: str,
        key: Optional[str],
        value: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Publish a message to a Kafka topic."""
        if not self._producer:
            logger.debug(f"Kafka not available, message dropped for topic: {topic}")
            return False

        try:
            kafka_headers = []
            if headers:
                kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

            # Add metadata headers
            kafka_headers.append(("source", b"alphaforge-backend"))
            kafka_headers.append(("timestamp", datetime.utcnow().isoformat().encode()))

            future = self._producer.send(
                topic=topic,
                key=key,
                value=value,
                headers=kafka_headers if kafka_headers else None,
            )

            # Wait for acknowledgment with timeout
            record_metadata = future.get(timeout=10)
            logger.debug(
                f"✅ Published to {topic} [partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}]"
            )
            return True

        except KafkaTimeoutError:
            logger.error(f"❌ Kafka publish timeout for topic: {topic}")
            return False
        except KafkaError as e:
            logger.error(f"❌ Kafka publish error for topic {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error publishing to {topic}: {e}")
            return False

    async def publish_market_price(
        self, asset: str, data: Dict[str, Any]
    ) -> bool:
        """Publish market price data."""
        return await self.publish(
            topic="market-prices",
            key=asset,
            value={
                "asset": asset,
                "price": data.get("price"),
                "volume": data.get("volume"),
                "timestamp": datetime.utcnow().isoformat(),
                **data,
            },
        )

    async def publish_signal(
        self, signal_id: str, signal_data: Dict[str, Any]
    ) -> bool:
        """Publish a generated signal."""
        return await self.publish(
            topic="signals-generated",
            key=signal_id,
            value={
                "signal_id": signal_id,
                **signal_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def publish_execution(
        self, user_id: str, execution_data: Dict[str, Any]
    ) -> bool:
        """Publish an execution event."""
        return await self.publish(
            topic="executions",
            key=user_id,
            value={
                "user_id": user_id,
                **execution_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def publish_position_update(
        self, user_id: str, position_data: Dict[str, Any]
    ) -> bool:
        """Publish a position update."""
        return await self.publish(
            topic="positions-updated",
            key=user_id,
            value={
                "user_id": user_id,
                **position_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def publish_kyc_event(
        self, user_id: str, event_data: Dict[str, Any]
    ) -> bool:
        """Publish a KYC event."""
        return await self.publish(
            topic="kyc-events",
            key=user_id,
            value={
                "user_id": user_id,
                **event_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def publish_audit_event(
        self, entity_id: str, audit_data: Dict[str, Any]
    ) -> bool:
        """Publish an audit event."""
        return await self.publish(
            topic="audit-events",
            key=entity_id,
            value={
                "entity_id": entity_id,
                **audit_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # ==========================================================================
    # Consumer Methods
    # ==========================================================================

    def subscribe(
        self,
        topic: str,
        handler: Callable,
        group_id: str,
        auto_offset_reset: str = "latest",
    ):
        """Subscribe to a Kafka topic with an async handler."""
        if not KAFKA_AVAILABLE:
            logger.warning(f"Kafka not available, cannot subscribe to: {topic}")
            return

        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda m: m.decode("utf-8") if m else None,
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )

            self._consumers[topic] = consumer

            # Start consumer in background thread
            loop = asyncio.get_event_loop()

            def _consume():
                try:
                    for message in consumer:
                        if not self._running:
                            break
                        try:
                            loop.call_soon_threadsafe(
                                asyncio.ensure_future,
                                handler(message.topic, message.key, message.value),
                            )
                        except Exception as e:
                            logger.error(f"Error processing message from {topic}: {e}")
                except Exception as e:
                    logger.error(f"Consumer error for {topic}: {e}")

            import threading
            thread = threading.Thread(target=_consume, daemon=True, name=f"kafka-{topic}")
            thread.start()

            logger.info(f"✅ Subscribed to topic: {topic} (group: {group_id})")

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to {topic}: {e}")

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check Kafka health."""
        if not self._producer:
            return {"status": "disconnected", "backend": "kafka"}

        try:
            metadata = self._producer.list_topics_metadata()
            return {
                "status": "healthy",
                "backend": "kafka",
                "topics": len(metadata.topics),
                "bootstrap_servers": self.bootstrap_servers,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "kafka",
                "error": str(e),
            }


# Global instance
kafka_service: Optional[KafkaService] = None


async def get_kafka_service() -> KafkaService:
    """Get or create the global Kafka service."""
    global kafka_service
    if kafka_service is None:
        import os
        kafka_service = KafkaService(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        )
        await kafka_service.initialize()
    return kafka_service
