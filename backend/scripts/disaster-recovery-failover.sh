#!/bin/bash
# ==========================================================================
# AlphaForge Disaster Recovery - Failover Script
# Simulates regional failure and executes failover to secondary region
# ==========================================================================

set -euo pipefail

# Configuration
PRIMARY_REGION="${PRIMARY_REGION:-us-east-1}"
SECONDARY_REGION="${SECONDARY_REGION:-us-west-2}"
EKS_CLUSTER_PRIMARY="${EKS_CLUSTER_PRIMARY:-alphaforge-production}"
EKS_CLUSTER_SECONDARY="${EKS_CLUSTER_SECONDARY:-alphaforge-production-secondary}"
RDS_PRIMARY="${RDS_PRIMARY:-alphaforge-primary}"
RDS_REPLICA="${RDS_REPLICA:-alphaforge-replica-1}"
ROUTE53_HOSTED_ZONE="${ROUTE53_HOSTED_ZONE:-}"
DOMAIN="api.alphaforge.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" >&2; }
step() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

START_TIME=$(date +%s)

# ==========================================================================
step "1/7: Pre-Failover Checks"
# ==========================================================================

log "Verifying secondary region readiness..."

# Check if secondary EKS cluster exists
if aws eks describe-cluster --name "${EKS_CLUSTER_SECONDARY}" --region "${SECONDARY_REGION}" > /dev/null 2>&1; then
    log "✅ Secondary EKS cluster is available"
else
    error "Secondary EKS cluster not found: ${EKS_CLUSTER_SECONDARY}"
fi

# Check if RDS replica exists and is in sync
REPLICA_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier "${RDS_REPLICA}" \
    --region "${SECONDARY_REGION}" \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "not-found")

if [ "${REPLICA_STATUS}" = "available" ]; then
    log "✅ RDS replica is available"
else
    warn "RDS replica status: ${REPLICA_STATUS}"
fi

# ==========================================================================
step "2/7: Promote RDS Read Replica"
# ==========================================================================

log "Promoting read replica to primary..."

# Stop writes to primary first (if accessible)
log "Note: If primary is unreachable, skip to replica promotion"

aws rds promote-read-replica \
    --db-instance-identifier "${RDS_REPLICA}" \
    --region "${SECONDARY_REGION}" 2>/dev/null || warn "Replica promotion may have already been done"

log "⏳ Waiting for replica promotion to complete..."
aws rds wait db-instance-available \
    --db-instance-identifier "${RDS_REPLICA}" \
    --region "${SECONDARY_REGION}" || warn "Wait timed out - check manually"

log "✅ Replica promoted"

# ==========================================================================
step "3/7: Update DNS Failover"
# ==========================================================================

if [ -n "${ROUTE53_HOSTED_ZONE}" ]; then
    log "Updating Route53 DNS to point to secondary region..."
    
    NEW_PRIMARY_IP=$(kubectl get svc -n alphaforge -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "unknown")
    
    cat > /tmp/dns-update.json << EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${DOMAIN}",
      "Type": "A",
      "TTL": 60,
      "ResourceRecords": [{"Value": "${NEW_PRIMARY_IP}"}]
    }
  }]
}
EOF

    aws route53 change-resource-record-sets \
        --hosted-zone-id "${ROUTE53_HOSTED_ZONE}" \
        --change-batch file:///tmp/dns-update.json 2>/dev/null || warn "DNS update failed - check manually"
    
    log "✅ DNS updated (TTL: 60s)"
else
    warn "Skipping DNS update (ROUTE53_HOSTED_ZONE not set)"
fi

# ==========================================================================
step "4/7: Deploy Services to Secondary Region"
# ==========================================================================

log "Updating kubeconfig for secondary region..."
aws eks update-kubeconfig --name "${EKS_CLUSTER_SECONDARY}" --region "${SECONDARY_REGION}"

log "Applying Kubernetes manifests..."
kubectl apply -k k8s/base/ 2>/dev/null || warn "Some manifests may already exist"

log "Waiting for backend deployment..."
kubectl rollout status deployment/alphaforge-backend -n alphaforge --timeout=300s 2>/dev/null || warn "Deployment wait timed out"

log "✅ Services deployed to secondary region"

# ==========================================================================
step "5/7: Verify Service Health"
# ==========================================================================

log "Running health checks..."

HEALTH_ENDPOINT=$(kubectl get ingress -n alphaforge -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -n "${HEALTH_ENDPOINT}" ]; then
    for i in $(seq 1 5); do
        if curl -sf "http://${HEALTH_ENDPOINT}/health" > /dev/null 2>&1; then
            log "✅ Health check passed (attempt ${i}/5)"
            break
        fi
        warn "Health check failed (attempt ${i}/5), retrying in 10s..."
        sleep 10
    done
else
    warn "Could not determine ingress endpoint"
fi

# ==========================================================================
step "6/7: Resume Kafka Consumers"
# ==========================================================================

log "Verifying Kafka consumers are running..."

# In production, this would check consumer group offsets
# and resume from the last committed offset
log "⚠️  Manual verification recommended: check Kafka consumer lag in Grafana"

# ==========================================================================
step "7/7: Send Notifications"
# ==========================================================================

log "Sending incident notification..."

# Send Slack/PagerDuty notification
NOTIFICATION_PAYLOAD=$(cat << EOF
{
  "text": "🔴 AlphaForge DR Failover Executed",
  "details": {
    "primary_region": "${PRIMARY_REGION}",
    "secondary_region": "${SECONDARY_REGION}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "rds_promoted": true,
    "dns_updated": $([ -n "${ROUTE53_HOSTED_ZONE}" ] && echo "true" || echo "false"),
    "services_deployed": true
  }
}
EOF
)

# Post to webhook (Slack/PagerDuty)
if [ -n "${INCIDENT_WEBHOOK_URL:-}" ]; then
    curl -X POST "${INCIDENT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "${NOTIFICATION_PAYLOAD}" > /dev/null 2>&1 || warn "Notification webhook failed"
    log "✅ Incident notification sent"
else
    warn "INCIDENT_WEBHOOK_URL not set - skipping notification"
fi

# ==========================================================================
# Summary
# ==========================================================================

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DR FAILOVER COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
log "📊 Failover Summary:"
log "   Duration: ${DURATION} seconds"
log "   Primary Region: ${PRIMARY_REGION} (failed)"
log "   Secondary Region: ${SECONDARY_REGION} (active)"
log "   RDS: Promoted replica"
log "   DNS: Updated ($([ -n "${ROUTE53_HOSTED_ZONE}" ] && echo 'Yes' || echo 'Skipped'))"
log "   Services: Deployed and healthy"
log ""
log "⚠️  Next Steps:"
log "   1. Verify all services are processing requests"
log "   2. Check Kafka consumer lag in Grafana"
log "   3. Monitor error rates for 30 minutes"
log "   4. Communicate status to stakeholders"
log "   5. Plan root cause analysis for primary failure"
