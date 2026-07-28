# AlphaForge Operations Runbook

## Quick Links

- **Dashboard:** https://grafana.alphaforge.internal
- **Alerts:** https://alertmanager.alphaforge.internal
- **Logs:** https://kibana.alphaforge.internal
- **Status Page:** https://status.alphaforge.example.com
- **Incident Response:** #incidents channel in Slack

---

## Common Operations

### Checking System Health

```bash
# Check cluster
kubectl get nodes,pods -n alphaforge

# Check pod status
kubectl get pods -n alphaforge -o wide

# Check for issues
kubectl get events -n alphaforge --sort-by='.lastTimestamp' | tail -20

# Resource usage
kubectl top pods -n alphaforge

# Service endpoints
kubectl get svc,ingress -n alphaforge
```

### Viewing Logs

```bash
# Recent logs
kubectl logs -f deployment/alphaforge-backend -n alphaforge

# Specific pod
kubectl logs -f pod/alphaforge-backend-xyz -n alphaforge

# Previous crashed pod
kubectl logs --previous pod/alphaforge-backend-xyz -n alphaforge

# All pods in deployment
kubectl logs -f deployment/alphaforge-backend -n alphaforge --all-containers

# Filter by level
kubectl logs deployment/alphaforge-backend -n alphaforge | grep ERROR

# CloudWatch logs
aws logs tail /aws/eks/alphaforge-production --follow
```

### Checking Database

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw rds_endpoint | cut -d: -f1)

# Connect to database
psql -h $DB_ENDPOINT -U alphaforge_admin -d alphaforge

# Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

# Check slow queries
SELECT 
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

# Check connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Vacuum and analyze
VACUUM ANALYZE;
```

### Checking Redis

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)

# Connect to Redis
redis-cli -h $REDIS_ENDPOINT

# Check status
INFO

# Monitor commands
MONITOR

# Check memory usage
INFO memory

# Get all keys
KEYS *

# Delete cache
FLUSHDB

# Check connectivity
PING
```

---

## Troubleshooting Guide

### Issue: Pod CrashLoopBackOff

**Symptoms:** Pod restarts repeatedly, not ready

```bash
# Check logs
kubectl logs <pod-name> -n alphaforge --previous

# Describe pod
kubectl describe pod <pod-name> -n alphaforge

# Check resource requests vs available
kubectl top nodes

# Check for OOMKilled
kubectl get pods -n alphaforge -o=custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,REASON:.status.containerStatuses[0].lastState.terminated.reason
```

**Common causes & fixes:**
- **OOMKilled:** Increase memory limit in deployment
- **Startup probe failure:** Database not ready, wait and retry
- **Missing secrets:** Create required secrets
- **Image pull error:** Check image registry access

### Issue: High CPU/Memory Usage

```bash
# Identify resource hogs
kubectl top pods -n alphaforge --sort-by=cpu

# Check metrics
kubectl top nodes --sort-by=cpu

# Scale up
kubectl scale deployment alphaforge-backend --replicas=5 -n alphaforge

# Check for memory leaks
kubectl logs deployment/alphaforge-backend -n alphaforge | grep -i memory

# Check for runaway processes
kubectl exec <pod> -- ps aux | sort -rnk 3,3 | head -5
```

### Issue: Database Connection Pool Exhausted

```bash
# Check connection count
psql -h $DB_ENDPOINT -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Check idle connections
psql -h $DB_ENDPOINT -c "SELECT * FROM pg_stat_activity WHERE state = 'idle';"

# Kill idle connections
psql -h $DB_ENDPOINT -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND query_start < NOW() - INTERVAL '30 minutes';
"

# Restart backend pods to reconnect
kubectl rollout restart deployment/alphaforge-backend -n alphaforge
```

### Issue: Slow Queries

```bash
# Enable slow query logging
SET log_min_duration_statement = 1000;

# Find slowest queries
SELECT 
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Explain slow query
EXPLAIN ANALYZE SELECT * FROM paper_trades WHERE user_id = 'xxx' ORDER BY created_at DESC LIMIT 10;

# Add index if needed
CREATE INDEX idx_paper_trades_user_created ON paper_trades(user_id, created_at DESC);

# Refresh stats
ANALYZE paper_trades;
```

### Issue: WebSocket Connections Failing

```bash
# Check pod logs for WebSocket errors
kubectl logs deployment/alphaforge-backend -n alphaforge | grep -i websocket

# Test WebSocket manually
wscat -c wss://api.alphaforge.example.com/ws/market-updates

# Check ingress configuration
kubectl get ingress alphaforge-ingress -n alphaforge -o yaml | grep -A 5 websocket

# Check proxy timeout settings
kubectl get deployment alphaforge-backend -n alphaforge -o yaml | grep -i timeout
```

---

## Performance Optimization

### Database Query Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_paper_trades_user_status ON paper_trades(user_id, status);
CREATE INDEX idx_signals_created_at_confidence ON signals(created_at DESC, confidence DESC);

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM portfolios WHERE user_id = 'xxx';

-- Use LIMIT for large result sets
SELECT * FROM trades WHERE user_id = 'xxx' ORDER BY created_at DESC LIMIT 100;

-- Batch operations when possible
INSERT INTO audit_logs (user_id, action) VALUES 
  ('user1', 'trade_executed'),
  ('user2', 'signal_approved'),
  ('user3', 'kyc_submitted');
```

### Cache Optimization

```bash
# Monitor cache hit rate
redis-cli --stat

# Clear old entries
redis-cli EVAL "
  local keys = redis.call('keys', 'signal:*')
  for i,key in ipairs(keys) do
    redis.call('del', key)
  end
" 0

# Set cache expiration
redis-cli EXPIRE signal:BTC-2026-07-05 300
```

### API Response Time Reduction

```bash
# Profile API endpoints
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/signals

# Check compression
curl -H "Accept-Encoding: gzip" -w "Time: %{time_total}\n" http://localhost:8000/api/signals

# Monitor backend metrics
curl http://localhost:8001/metrics | grep http_request_duration_seconds_bucket
```

---

## Monitoring & Alerting

### Key Metrics to Watch

```
Backend:
  - API latency (p99 < 2s)
  - Error rate (< 1%)
  - Request throughput
  - Database connection count
  - Memory usage

Frontend:
  - Page load time (< 3s)
  - API call latency
  - Error rate
  - User sessions

Database:
  - Query latency (p99 < 100ms)
  - Connections used / max
  - CPU utilization
  - Disk space
  - Replication lag
```

### Setting Up Custom Alerts

```bash
# SSH into monitoring pod
kubectl exec -it deployment/prometheus -n monitoring -- /bin/sh

# Edit prometheus config
kubectl edit configmap prometheus-config -n monitoring

# Add alert rule
cat << EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: alphaforge-alerts
  namespace: monitoring
spec:
  groups:
  - name: alphaforge
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"
EOF
```

---

## Incident Response

### Incident Notification

1. Check #incidents channel in Slack
2. Create incident in incident management system
3. Page on-call engineer if P1

### Common Incidents & Fixes

**P1: All APIs Down**
```bash
# Step 1: Check cluster health
kubectl get nodes,pods -n alphaforge

# Step 2: Check for node issues
kubectl describe nodes | grep -i "not ready"

# Step 3: Restart cluster
aws eks update-nodegroup-config \
  --cluster-name alphaforge-production \
  --nodegroup-name alphaforge-production \
  --desired-size 3

# Step 4: Check again
kubectl get pods -n alphaforge
```

**P2: Database Slow/Unavailable**
```bash
# Step 1: Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier alphaforge-production

# Step 2: Check connections
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Step 3: Kill idle connections
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Step 4: Failover if needed
aws rds failover-db-cluster \
  --db-cluster-identifier alphaforge-production
```

**P3: High Latency/Timeouts**
```bash
# Step 1: Check resource usage
kubectl top pods -n alphaforge

# Step 2: Scale if needed
kubectl scale deployment alphaforge-backend --replicas=5 -n alphaforge

# Step 3: Monitor
watch kubectl get pods -n alphaforge

# Step 4: Analyze logs
kubectl logs deployment/alphaforge-backend -n alphaforge | tail -100
```

### Post-Incident

- [ ] Update status page
- [ ] Document root cause
- [ ] Create ticket for prevention
- [ ] Update runbook if needed
- [ ] Schedule post-mortem
- [ ] Notify stakeholders

---

## Scheduled Maintenance

### Daily Tasks

```bash
# Check logs for errors
kubectl logs deployment/alphaforge-backend -n alphaforge | grep ERROR | wc -l

# Verify backups completed
aws rds describe-db-snapshots \
  --db-instance-identifier alphaforge-production \
  --query 'DBSnapshots[0].[SnapshotCreateTime,Status]'

# Monitor disk space
aws rds describe-db-instances \
  --db-instance-identifier alphaforge-production \
  --query 'DBInstances[0].[AllocatedStorage,DBInstanceClass]'
```

### Weekly Tasks

```bash
# Analyze database
psql -h $DB_ENDPOINT -d alphaforge -c "ANALYZE;"

# Check table sizes
psql -h $DB_ENDPOINT -d alphaforge -c "
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;"

# Test backup restore
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier alphaforge-test-restore \
  --db-snapshot-identifier $(aws rds describe-db-snapshots \
    --query 'DBSnapshots[0].DBSnapshotIdentifier' --output text)
```

### Monthly Tasks

```bash
# Review security groups
aws ec2 describe-security-groups --filters Name=group-id,Values=sg-*

# Check certificate expiry
kubectl get certificate -n alphaforge

# Review cost
aws ce get-cost-and-usage \
  --time-period Start=2026-06-01,End=2026-07-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost

# Rotate secrets
aws secretsmanager rotate-secret --secret-id alphaforge-db-password

# Update dependencies
kubectl set image deployment/alphaforge-backend \
  backend=ghcr.io/alphaforge/backend:latest -n alphaforge
```

---

## Useful Commands Cheatsheet

```bash
# Cluster info
kubectl cluster-info
kubectl api-resources

# Get resources
kubectl get pods,svc,ingress -n alphaforge
kubectl describe pod <pod-name> -n alphaforge

# Execute commands
kubectl exec -it <pod-name> -n alphaforge -- bash
kubectl exec <pod-name> -n alphaforge -- python -m pytest

# Scale
kubectl scale deployment <name> --replicas=5 -n alphaforge

# Edit
kubectl edit deployment <name> -n alphaforge
kubectl patch deployment <name> -p '{"spec":{"replicas":5}}' -n alphaforge

# Logs
kubectl logs -f deployment/<name> -n alphaforge
kubectl logs <pod-name> -c <container> -n alphaforge

# Port forward
kubectl port-forward svc/<service> 8000:8000 -n alphaforge

# Copy files
kubectl cp alphaforge/<pod>:/path/to/file ./local-file
kubectl cp ./local-file alphaforge/<pod>:/path/to/file

# Delete
kubectl delete pod <pod-name> -n alphaforge
kubectl rollout restart deployment <name> -n alphaforge

# Dry run
kubectl apply -f manifest.yaml --dry-run=client
```

---

**Version:** 1.0  
**Last Updated:** 2026-07-05  
**On-Call Rotation:** Slack /oncall
