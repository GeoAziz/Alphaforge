# AlphaForge Deployment & Operations Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Deployment](#production-deployment)
3. [Scaling Guide](#scaling-guide)
4. [Monitoring](#monitoring)
5. [Incident Response](#incident-response)
6. [Backup & Recovery](#backup--recovery)
7. [Maintenance](#maintenance)

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing locally
- [ ] No console errors/warnings
- [ ] Code reviewed by 2+ team members
- [ ] No hardcoded secrets or API keys
- [ ] Performance benchmarks meet targets
- [ ] Security scan completed (SAST)

### Configuration
- [ ] Environment variables configured
- [ ] Database migrations prepared
- [ ] Redis cache configured
- [ ] CDN cache headers set
- [ ] SSL certificates valid
- [ ] API rate limits configured

### Infrastructure
- [ ] Load balancers configured
- [ ] Auto-scaling policies set
- [ ] Backup systems tested
- [ ] Monitoring alerts configured
- [ ] Log aggregation enabled
- [ ] VPN/Security groups locked down

### Documentation
- [ ] Release notes prepared
- [ ] User communication drafted
- [ ] Rollback procedure documented
- [ ] Known issues documented

## Production Deployment

### Frontend Deployment (Vercel)

```bash
# Build optimized production bundle
npm run build

# Test production build locally
npm run start

# Deploy to staging first
vercel --prod --token $VERCEL_TOKEN

# Run smoke tests on staging
npm run test:e2e -- --baseUrl=https://staging.alphaforge.com

# Deploy to production
vercel promote staging-deployment-id

# Monitor deployment
vercel inspect --prod
```

### Backend Deployment (Railway/Render)

```bash
# Build Docker image
docker build -t alphaforge-api:latest .

# Push to registry
docker push gcr.io/alphaforge/api:latest

# Deploy to production
gcloud run deploy alphaforge-api \
  --image gcr.io/alphaforge/api:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DB_URL,REDIS_URL=$REDIS_URL

# Monitor logs
gcloud run logs read alphaforge-api --limit 50
```

### Database Migrations

```bash
# Create backup before migrations
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Run migrations
alembic upgrade head

# Verify migrations
alembic current

# Rollback if needed
alembic downgrade -1
```

### Zero-Downtime Deployment

```bash
# 1. Deploy new version with both old & new code
kubectl set image deployment/api \
  api=gcr.io/alphaforge/api:v2.0 --record

# 2. Monitor new pods
kubectl rollout status deployment/api

# 3. Verify health
curl -s https://api.alphaforge.com/health | jq .status

# 4. Complete rollover
kubectl rollout resume deployment/api

# 5. Monitor for 30 minutes
# If issues, rollback:
kubectl rollout undo deployment/api
```

## Scaling Guide

### Horizontal Scaling

**API Servers:**
```yaml
# Scale to 3 replicas
kubectl scale deployment api --replicas=3

# Auto-scaling based on CPU
kubectl autoscale deployment api \
  --min=3 \
  --max=10 \
  --cpu-percent=70
```

**Database:**
```sql
-- Create read replicas for scaling reads
ALTER SYSTEM SET max_connections = 500;
SELECT pg_reload_conf();

-- Monitor connections
SELECT sum(numbackends) FROM pg_stat_database;
```

**Cache:**
```bash
# Scale Redis cluster
redis-cli --cluster add-node new-node:6379 existing-node:6379
redis-cli --cluster reshard existing-node:6379
```

### Vertical Scaling

When horizontal scaling isn't sufficient:

```bash
# Increase pod resources
kubectl set resources deployment api \
  --limits=cpu=2,memory=2Gi \
  --requests=cpu=1,memory=1Gi

# Monitor resource usage
kubectl top nodes
kubectl top pods -l app=api
```

## Monitoring

### Key Metrics to Monitor

```yaml
Alerts:
  - API Response Time > 500ms
  - Error Rate > 1%
  - Database Query Time > 1000ms
  - Cache Hit Rate < 80%
  - Memory Usage > 80%
  - Disk Usage > 90%
  - Pod Restarts > 0/hour
  - Failed Deployments
```

### Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database connections
pg_stat_activity_count

# Cache hit rate
redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses)
```

### Dashboard Setup

Create Grafana dashboards for:
1. Request rates & latency
2. Error rates by endpoint
3. Database performance
4. Cache efficiency
5. Resource utilization
6. User growth metrics

### Log Aggregation

```bash
# Query logs in Cloud Logging
gcloud logging read "severity>=ERROR" --limit 50

# Real-time log streaming
kubectl logs -f deployment/api

# Log patterns for errors
kubectl logs deployment/api | grep "ERROR" | sort | uniq -c
```

## Incident Response

### High Error Rate (>5%)

```bash
# 1. Check API health
curl -s https://api.alphaforge.com/health | jq .

# 2. View recent errors
kubectl logs deployment/api --tail=100 | grep ERROR

# 3. Check database
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# 4. Check external services
curl -s https://status.binance.com | jq .

# 5. If code issue, rollback
kubectl rollout undo deployment/api

# 6. Scale down to single pod for debugging
kubectl scale deployment api --replicas=1
```

### Database Performance Degradation

```bash
# 1. Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

# 2. Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables ORDER BY pg_total_relation_size DESC;

# 3. Analyze tables
ANALYZE;

# 4. Check connection count
SELECT count(*) FROM pg_stat_activity;

# 5. If needed, increase max_connections
ALTER SYSTEM SET max_connections = 500;
SELECT pg_reload_conf();
```

### Memory Leak Detection

```bash
# 1. Monitor memory over time
kubectl top pods -l app=api --containers

# 2. Check for memory leaks
# In pod: heap dump
jcmd 1 GC.heap_dump /tmp/heap.hprof

# 3. Analyze heap
jhat -J-Xmx2g /tmp/heap.hprof

# 4. If confirmed, restart pod
kubectl rollout restart deployment/api
```

### Rollback Procedure

```bash
# 1. Identify previous working version
kubectl rollout history deployment/api

# 2. Rollback to previous
kubectl rollout undo deployment/api

# 3. Monitor rollback
kubectl rollout status deployment/api

# 4. Verify health after rollback
curl -s https://api.alphaforge.com/health

# 5. Notify team & investigate
echo "Rolled back to previous version. Investigating..."
```

## Backup & Recovery

### Daily Backups

```bash
# Automated daily at 2 AM UTC
# Configure in Cloud SQL:
gcloud sql backups create --instance=alphaforge-db

# List backups
gcloud sql backups list --instance=alphaforge-db

# Backup retention: 30 days
gcloud sql instances patch alphaforge-db \
  --backup-start-time 02:00
```

### Disaster Recovery

```bash
# 1. Restore from backup
gcloud sql backups restore BACKUP_ID --backup-instance=alphaforge-db

# 2. Restore from point-in-time
gcloud sql backups restore --backup-instance=alphaforge-db \
  --point-in-time=2024-01-15T10:30:00Z

# 3. Verify restored data
psql $RESTORED_DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# 4. Update connection strings
kubectl set env deployment/api DATABASE_URL=$NEW_DATABASE_URL

# 5. Test application
npm run test:integration
```

### Data Consistency Checks

```sql
-- Check for orphaned records
SELECT COUNT(*) FROM trades WHERE user_id NOT IN (SELECT id FROM users);

-- Verify signal integrity
SELECT symbol, COUNT(*) 
FROM signals 
GROUP BY symbol 
HAVING COUNT(*) > 10000;

-- Check for duplicate transactions
SELECT transaction_id, COUNT(*) 
FROM transactions 
GROUP BY transaction_id 
HAVING COUNT(*) > 1;
```

## Maintenance

### Weekly Tasks

- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Verify backups completed
- [ ] Update dependencies (security patches)
- [ ] Review user feedback

### Monthly Tasks

- [ ] Load testing (simulate peak usage)
- [ ] Security scan (dependency audit)
- [ ] Database optimization (analyze & vacuum)
- [ ] Cost optimization review
- [ ] Capacity planning review

### Quarterly Tasks

- [ ] Full disaster recovery drill
- [ ] Architecture review
- [ ] Performance optimization review
- [ ] Security audit
- [ ] Compliance review

### System Maintenance Window

Schedule: **2nd Sunday, 2:00-4:00 AM UTC**

```bash
# 1. Enable maintenance mode
kubectl set env deployment/api MAINTENANCE_MODE=true

# 2. Notify users
POST /api/notifications (broadcast)

# 3. Run maintenance tasks
- Database VACUUM & ANALYZE
- Update dependencies
- Clear old logs
- Optimize indexes

# 4. Run tests
npm run test:full

# 5. Disable maintenance mode
kubectl set env deployment/api MAINTENANCE_MODE=false

# 6. Verify all systems
curl https://api.alphaforge.com/health
```

## Performance Optimization

### Frontend Optimizations

```bash
# Build analysis
npm run build -- --analyze

# Code splitting
npm run build -- --chunk-size-warning-limit=500

# Image optimization
npx imagemin src/images/** --out-dir=dist/images

# Monitor Web Vitals
# LCP < 2.5s
# FID < 100ms  
# CLS < 0.1
```

### Backend Optimizations

```python
# Database query optimization
EXPLAIN ANALYZE SELECT * FROM signals WHERE created_at > NOW() - '7 days'::interval;

# Add indexes
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_trades_user_id ON trades(user_id, created_at);

# Monitor slow queries
log_min_duration_statement = 1000  # 1 second

# Cache frequently accessed data
CACHE_TTL = 300  # 5 minutes for tickers
```

### Cost Optimization

```bash
# Use spot instances for non-critical workloads
kubectl patch deployment api -p \
  '{"spec":{"template":{"spec":{"nodeSelector":{"cloud.google.com/gke-spot":"true"}}}}}'

# Right-size resources
# Actual vs requested: CPU 40%, Memory 60%
# Reduce resource requests by 20-30%

# Use CDN for static assets
# Reduces origin bandwidth by 80%+

# Archive old data
DELETE FROM audit_logs WHERE created_at < NOW() - '1 year'::interval;
```
