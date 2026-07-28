#!/bin/bash
# ==========================================================================
# AlphaForge Runbook: Manual Database Failover
# Use when the primary PostgreSQL instance is down
# ==========================================================================

set -euo pipefail

# Configuration
PRIMARY_ID="${RDS_PRIMARY:-alphaforge-primary}"
REPLICA_ID="${RDS_REPLICA:-alphaforge-replica-1}"
REGION="${AWS_REGION:-us-east-1}"
SECRET_ID="${DB_SECRET_ID:-prod/db/postgres}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" >&2; }

# ==========================================================================
# Step 1: Check primary status
# ==========================================================================

log "Checking primary database status..."
PRIMARY_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier "${PRIMARY_ID}" \
    --region "${REGION}" \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "not-found")

log "Primary status: ${PRIMARY_STATUS}"

if [ "${PRIMARY_STATUS}" = "available" ]; then
    warn "Primary is still available. Are you sure you want to failover?"
    read -p "Type 'yes' to continue: " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        log "Aborted."
        exit 0
    fi
fi

# ==========================================================================
# Step 2: Promote read replica
# ==========================================================================

log "Promoting read replica: ${REPLICA_ID}..."
aws rds promote-read-replica \
    --db-instance-identifier "${REPLICA_ID}" \
    --region "${REGION}"

log "⏳ Waiting for promotion to complete..."
aws rds wait db-instance-available \
    --db-instance-identifier "${REPLICA_ID}" \
    --region "${REGION}"

NEW_PRIMARY_HOST=$(aws rds describe-db-instances \
    --db-instance-identifier "${REPLICA_ID}" \
    --region "${REGION}" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

log "✅ Replica promoted. New primary: ${NEW_PRIMARY_HOST}"

# ==========================================================================
# Step 3: Update connection strings in Secrets Manager
# ==========================================================================

log "Updating Secrets Manager with new connection info..."
aws secretsmanager update-secret \
    --secret-id "${SECRET_ID}" \
    --region "${REGION}" \
    --secret-string "{\"host\":\"${NEW_PRIMARY_HOST}\",\"port\":5432,\"database\":\"alphaforge\"}"

log "✅ Secrets Manager updated"

# ==========================================================================
# Step 4: Restart application pods
# ==========================================================================

log "Restarting application pods to pick up new connection string..."
kubectl rollout restart deployment/alphaforge-backend -n alphaforge
kubectl rollout status deployment/alphaforge-backend -n alphaforge --timeout=300s

log "✅ Pods restarted"

# ==========================================================================
# Step 5: Verify connectivity
# ==========================================================================

log "Verifying database connectivity..."
# Run a quick health check
kubectl exec -n alphaforge deployment/alphaforge-backend -- \
    python -c "import psycopg2; conn = psycopg2.connect(host='${NEW_PRIMARY_HOST}', dbname='alphaforge'); print('Connected OK'); conn.close()"

log "✅ Database failover complete"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  FAILOVER COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
log "New primary: ${NEW_PRIMARY_HOST}"
log "Verify services: kubectl get pods -n alphaforge"
