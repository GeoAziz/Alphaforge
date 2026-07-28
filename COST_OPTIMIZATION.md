# Cost Optimization Guide for AlphaForge

## Current Monthly Costs

| Component | Cost | Optimization |
|-----------|------|--------------|
| EKS Cluster | $1,200 | Reserved instances, spot instances |
| RDS Database | $400 | Smaller instance, storage optimization |
| Redis Cache | $150 | Smaller nodes, consolidation |
| S3 Storage | $100 | Lifecycle policies, compression |
| Data Transfer | $200 | CloudFront CDN, regional endpoints |
| **Total** | **$2,050** | Potential savings: **$600/month (29%)** |

---

## Cost Optimization Strategies

### 1. Compute Optimization ($300/month savings)

#### Reserved Instances
```bash
# Calculate savings
aws ce get-reservation-purchase-recommendation \
  --service "Amazon EC2" \
  --lookback-period ONE_MONTH \
  --payment-option ALL_UPFRONT

# Purchase reserved instance
# 1-year: 30% discount
# 3-year: 45% discount
```

**Action Items:**
- [ ] Purchase 1-year reserved instances for baseline load
- [ ] Use spot instances for burstable workloads
- [ ] Rightsize instances based on actual usage

**Expected Savings:** $200-300/month

#### Spot Instances
```bash
# Use spot instances for non-critical workloads
# Current: 3x t3.large on-demand = $900/month
# With spot: 3x t3.large spot = $270/month
# Savings: $630/month (70%)

# Recommendation:
# - 2x reserved t3.large for production
# - 3x spot t3.large for burst capacity
# - Fallback to on-demand if spot unavailable
```

### 2. Database Optimization ($150/month savings)

#### Right-sizing RDS Instance
```bash
# Current: db.t3.medium ($0.34/hour) = $250/month

# Option 1: db.t3.small ($0.17/hour) = $125/month
# If traffic < 50% CPU most of the time

# Check current usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=alphaforge-production \
  --start-time 2026-06-01T00:00:00Z \
  --end-time 2026-07-05T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum | grep -E 'Average|Maximum' | awk '{sum+=$NF} END {print sum/NR}'
```

**Action Items:**
- [ ] Monitor CPU/Memory usage for 2 weeks
- [ ] If avg < 50%, downgrade to db.t3.small
- [ ] Use burst-capable instances for predictable spikes
- [ ] Enable automated backups pruning (>30 days)

**Expected Savings:** $125/month

#### Storage Optimization
```sql
-- Check table sizes
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Archive old trades (> 1 year)
DELETE FROM paper_trades 
WHERE closed_at < NOW() - INTERVAL '1 year'
AND status = 'CLOSED';

-- Reclaim space
VACUUM ANALYZE;

-- Current: 100GB allocated
-- After optimization: 50GB allocated
-- Savings: $5/month (storage)
```

### 3. Cache Optimization ($100/month savings)

#### Reduce Replica Count
```bash
# Current: 3 replicas x cache.t3.micro = $30 x 3 = $90/month

# Option: 1 primary + 1 replica
# Cost: $30 x 2 = $60/month
# Savings: $30/month

# Trade-off: Reduce HA from 3-node to 2-node
# Risk: Acceptable if we have automated recovery

aws elasticache modify-replication-group \
  --replication-group-id alphaforge-production \
  --num-cache-clusters 2 \
  --apply-immediately
```

**Action Items:**
- [ ] Reduce from 3 to 2 nodes (still HA)
- [ ] Monitor for performance impact
- [ ] Keep auto-failover enabled

**Expected Savings:** $30/month

#### Cache Eviction Policies
```bash
# Set memory limits and eviction policy
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor cache efficiency
redis-cli INFO stats | grep -E 'hits|misses'

# Target: > 95% hit rate
# If < 95%, increase cache size or optimize queries
```

### 4. Storage Optimization ($50/month savings)

#### S3 Lifecycle Policies
```bash
# Move objects to cheaper storage classes
aws s3api put-bucket-lifecycle-configuration \
  --bucket alphaforge-trading-data-prod \
  --lifecycle-configuration '{
    "Rules": [
      {
        "Id": "Archive old data",
        "Status": "Enabled",
        "Transitions": [
          {
            "Days": 30,
            "StorageClass": "STANDARD_IA"
          },
          {
            "Days": 90,
            "StorageClass": "GLACIER"
          }
        ],
        "Expiration": {
          "Days": 2555
        }
      }
    ]
  }'

# Cost breakdown:
# Standard (current): 100GB x $0.023 = $2.30/month
# Standard-IA: $0.0125/GB + $0.01/1000 requests = $1.25 + $0.50 = $1.75/month
# Glacier: $0.004/GB = $0.40/month
# Monthly savings: ~$0.50
```

#### Compress Data
```bash
# Enable gzip compression in application
# Reduce S3 object size by 70%
# Savings: ~$30/month

# Example (Python):
import gzip
with gzip.open('data.json.gz', 'wb') as f:
    f.write(json_data.encode())
```

### 5. Data Transfer Optimization ($100/month savings)

#### CloudFront CDN
```bash
# Cloudfront egress: $0.085/GB (vs $0.09/GB direct)
# Savings: 5% + reduced origin load

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "alphaforge-2026",
  "Comment": "AlphaForge static content",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3Origin",
        "DomainName": "alphaforge.s3.amazonaws.com",
        "S3OriginConfig": {}
      }
    ]
  },
  "DefaultCacheBehavior": {
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "Cached Methods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "ViewerProtocolPolicy": "redirect-to-https",
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  }
}'

# Expected savings: $100/month (reduced egress)
```

### 6. Monitoring & Alerting Cost Reduction

#### Consolidate Observability
```bash
# Current stack:
# - Prometheus: Self-hosted on EKS
# - Grafana: Self-hosted on EKS
# - Sentry: SaaS ($50/month for 10k errors)
# - Jaeger: Self-hosted on EKS

# Cost: Mostly infrastructure (covered above)
# Action: Archive logs to S3 vs ELK
# Savings: ~$100/month
```

---

## Cost Monitoring & Alerts

### AWS Cost Anomaly Detection
```bash
# Enable anomaly detection
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "AlphaForge-Monitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Create alert
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "AlphaForge-Alerts",
    "Threshold": 100,
    "Frequency": "DAILY",
    "MonitorArnList": ["arn:aws:ce:..."],
    "Subscribers": [
      {
        "Type": "SNS",
        "Address": "ops@alphaforge.com"
      }
    ]
  }'
```

### Monthly Cost Report
```bash
# Generate monthly cost report
aws ce get-cost-and-usage \
  --time-period Start=2026-06-01,End=2026-07-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output table

# Compare with previous month
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-06-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --output table
```

---

## Implementation Timeline

### Week 1: Quick Wins ($50/month)
- [ ] Enable S3 lifecycle policies
- [ ] Reduce Redis nodes to 2

### Week 2: Reserved Instances ($200/month)
- [ ] Monitor current compute usage
- [ ] Purchase 1-year reserved instances

### Week 3: Database Optimization ($125/month)
- [ ] Downgrade RDS if usage < 50% CPU
- [ ] Archive old trades
- [ ] Run VACUUM ANALYZE

### Week 4: Data Transfer ($100/month)
- [ ] Deploy CloudFront CDN
- [ ] Update DNS to point to CloudFront

### Month 2: Fine-tuning ($125/month)
- [ ] Implement spot instances for burst
- [ ] Consolidate monitoring stack
- [ ] Archive excess logs

---

## Cost Monitoring Dashboard

Create Grafana dashboard with these metrics:

```promql
# Monthly spend estimate
sum(aws_billing_total_bytes) * 0.000001 * hourly_rate

# Cost per API call
aws_cost / http_requests_total

# Cost per trade executed
aws_cost / trades_executed_total

# Cost per user
aws_cost / active_users

# Database cost efficiency
rds_cost / database_queries_total
```

---

## Estimated Monthly Cost After Optimization

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Compute | $1,200 | $700 | $500 |
| Database | $400 | $250 | $150 |
| Cache | $150 | $120 | $30 |
| Storage | $100 | $50 | $50 |
| Data Transfer | $200 | $100 | $100 |
| **Total** | **$2,050** | **$1,220** | **$830 (40%)** |

**Cost Per User (1000 active users):**
- Before: $2.05/user/month
- After: $1.22/user/month
- Savings: $0.83/user/month

---

## Cost Alerts & Thresholds

```bash
# Alert if daily cost exceeds threshold
DAILY_THRESHOLD=100  # $100/day = ~$3000/month

# Alert if cost increased 20% week-over-week
WEEKLY_INCREASE_THRESHOLD=20
```

---

**Review Frequency:** Monthly  
**Cost Review Meeting:** 1st Tuesday of each month  
**Budget Owner:** DevOps Team  
**Finance Approval Required:** Changes > $500/month
