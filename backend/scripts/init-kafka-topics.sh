#!/bin/bash
# ==========================================================================
# AlphaForge Kafka Topic Initialization Script
# Run this after Kafka is healthy to create all required topics
# ==========================================================================

set -euo pipefail

KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
WAIT_TIMEOUT=60

echo "⏳ Waiting for Kafka to be ready at ${KAFKA_BOOTSTRAP}..."
start_time=$(date +%s)

while ! kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" --list > /dev/null 2>&1; do
    elapsed=$(( $(date +%s) - start_time ))
    if [ "$elapsed" -ge "$WAIT_TIMEOUT" ]; then
        echo "❌ Timeout waiting for Kafka to be ready"
        exit 1
    fi
    echo "  Waiting... (${elapsed}s/${WAIT_TIMEOUT}s)"
    sleep 2
done

echo "✅ Kafka is ready"

# ==========================================================================
# Create Topics
# ==========================================================================

echo ""
echo "📦 Creating Kafka topics..."

# Market prices - real-time price data
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic market-prices \
    --partitions 10 \
    --replication-factor 1 \
    --config retention.ms=3600000 \
    --config cleanup.policy=delete
echo "  ✅ market-prices (10 partitions, 1h retention)"

# Signals generated
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic signals-generated \
    --partitions 20 \
    --replication-factor 1 \
    --config retention.ms=86400000 \
    --config cleanup.policy=delete
echo "  ✅ signals-generated (20 partitions, 24h retention)"

# Execution events
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic executions \
    --partitions 20 \
    --replication-factor 1 \
    --config retention.ms=86400000 \
    --config cleanup.policy=delete
echo "  ✅ executions (20 partitions, 24h retention)"

# Position updates
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic positions-updated \
    --partitions 10 \
    --replication-factor 1 \
    --config retention.ms=86400000 \
    --config cleanup.policy=delete
echo "  ✅ positions-updated (10 partitions, 24h retention)"

# KYC events
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic kyc-events \
    --partitions 5 \
    --replication-factor 1 \
    --config retention.ms=2592000000 \
    --config cleanup.policy=delete
echo "  ✅ kyc-events (5 partitions, 30 day retention)"

# Marketplace events
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic marketplace-events \
    --partitions 5 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete
echo "  ✅ marketplace-events (5 partitions, 7 day retention)"

# Audit events (long retention)
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" \
    --create --if-not-exists \
    --topic audit-events \
    --partitions 5 \
    --replication-factor 1 \
    --config retention.ms=7776000000 \
    --config cleanup.policy=delete
echo "  ✅ audit-events (5 partitions, 90 day retention)"

# ==========================================================================
# Verify Topics
# ==========================================================================

echo ""
echo "📋 Listing all topics:"
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP}" --list

echo ""
echo "✅ All Kafka topics created successfully"
