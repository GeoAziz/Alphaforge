# AlphaForge Architecture Documentation

## Executive Summary

AlphaForge is a production-grade cryptocurrency trading and portfolio management platform built on modern cloud-native technologies. It processes real-time market data, executes trading signals, manages portfolios, and provides AI-powered insights to institutional and retail traders.

**Stack Summary:**
- **Frontend:** Next.js 15 (React, TypeScript, Tailwind CSS)
- **Backend:** FastAPI (Python 3.10+, async/await)
- **Database:** PostgreSQL 15 with RLS policies
- **Cache:** Redis 7 with cluster support
- **Streaming:** Kafka for event processing
- **Analytics:** ClickHouse for OLAP queries
- **Infrastructure:** AWS EKS, RDS, ElastiCache, S3
- **Deployment:** Kubernetes, Terraform, GitHub Actions

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CDN / WAF / DDoS Protection             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Application Load Balancer (ALB)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                    │                        │                   │
│         ┌──────────┴────────┐      ┌────────┴──────────┐       │
│         │                   │      │                   │        │
│  ┌──────▼────────┐  ┌──────▼────────┐  ┌──────▼────────┐      │
│  │   Frontend    │  │   Backend     │  │  WebSocket    │      │
│  │  (Next.js)    │  │   (FastAPI)   │  │   Gateway     │      │
│  │  3 replicas   │  │  3 replicas   │  │  3 replicas   │      │
│  └──────┬────────┘  └──────┬────────┘  └──────┬────────┘      │
│         │                  │                    │               │
│         └──────────────────┼────────────────────┘               │
│                            │                                    │
│                    ┌───────┴───────┐                            │
│                    │               │                            │
│              ┌─────▼────┐  ┌──────▼─────┐                      │
│              │PostgreSQL│  │   Redis    │                      │
│              │   RDS    │  │ ElastiCache│                      │
│              └──────────┘  └────────────┘                      │
│                    │               │                            │
│              ┌─────▼────┐  ┌──────▼─────┐                      │
│              │  Kafka   │  │ClickHouse  │                      │
│              │(MSK)     │  │            │                      │
│              └──────────┘  └────────────┘                      │
│                                                                  │
│         ┌──────────────────────────────────────────┐            │
│         │      Monitoring & Logging                │            │
│         │  Prometheus │ Grafana │ CloudWatch      │            │
│         │  Sentry     │ Jaeger  │ ELK             │            │
│         └──────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Architecture

**Technology:** Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, Radix UI

**Key Features:**
- Server-side rendering (SSR) for SEO
- Static generation (SSG) for public pages
- API routes for backend integration
- Real-time updates via WebSockets
- Responsive design (mobile-first)

**Pages:**
- `/dashboard` - User overview and analytics
- `/portfolio` - Holdings, positions, P&L
- `/signals` - Active trading signals
- `/strategies` - Strategy management and marketplace
- `/backtesting` - Historical performance testing
- `/marketplace` - Creator strategies and copy trading
- `/settings` - User preferences and compliance

**State Management:**
- React hooks for component state
- Context API for global state
- TanStack Query for server state
- Zustand for client store (if needed)

---

### Backend Architecture

**Technology:** FastAPI (Python 3.10), async/await, Pydantic v2

**Service Layer (12+ Services):**

1. **AuthenticationService** - Firebase integration, token verification
2. **PortfolioService** - Position tracking, P&L calculation
3. **PaperTradingEngine** - Simulated execution with realistic slippage
4. **RiskManager** - Position sizing, liquidation, exposure limits
5. **SignalAggregator** - Multi-source signal collection
6. **SignalProcessor** - Validation, scoring, ranking
7. **BacktestingService** - Historical performance testing
8. **MarketDataService** - Real-time price feeds (Binance, etc.)
9. **ChatService** - AI-powered user assistance
10. **CreatorMarketplaceService** - Strategy sharing and copy trading
11. **KYCService** - Compliance and user verification
12. **NotificationService** - Alerts and messaging

**API Layers:**
- **Public API** - `/api/public/*` (unauthenticated)
- **Protected API** - `/api/frontend/*` (authenticated users)
- **Admin API** - `/api/admin/*` (admin only)
- **WebSocket** - `/ws/*` (real-time updates)
- **Webhook** - `/api/webhook/*` (external integrations)

**Database Schema:**
- `users` - User profiles and account info
- `portfolios` - Portfolio summaries and metrics
- `positions` - Open positions
- `paper_trades` - Trade history (open/closed)
- `signals` - Trading signals from all sources
- `strategies` - User-created and marketplace strategies
- `chat_messages` - User interactions with AI
- Plus 10+ more tables for compliance, performance, and analytics

**Async Patterns:**
- All database operations are async (AsyncIO)
- WebSocket connections for real-time updates
- Background tasks with Celery/RQ
- Event streaming with Kafka

---

## Data Flow

### Trading Execution Flow

```
1. Market Data (Binance WebSocket)
   ↓
2. SignalAggregator (collect from multiple sources)
   ├─ Internal ML models
   ├─ TradingView webhooks
   ├─ Community signals
   └─ External APIs
   ↓
3. SignalProcessor (validate & score)
   ├─ Backtesting validation
   ├─ Confidence scoring
   └─ Risk assessment
   ↓
4. User Interface (display signals)
   ↓
5. User Approval → Execute Trade
   ↓
6. PaperTradingEngine (simulation)
   ├─ Realistic slippage
   ├─ Position sizing checks
   └─ Risk limit validation
   ↓
7. Database (persist trade record)
   ↓
8. PortfolioService (update metrics)
   ├─ P&L calculation
   ├─ Exposure limits
   └─ Performance tracking
   ↓
9. Real-time Updates (WebSocket)
   └─ Portfolio, positions, P&L
```

### Risk Management Flow

```
Position Opening
  ↓
RiskManager validates:
  ├─ Position size (2% max per position)
  ├─ Exposure limits (20% per asset)
  ├─ Portfolio exposure (100% max)
  └─ Margin requirements
  ↓
If valid → Execute
If invalid → Reject with reason
  ↓
Monitor in real-time:
  ├─ Unrealized P&L
  ├─ Stop loss triggers
  ├─ Liquidation levels
  └─ Margin calls
  ↓
Auto-close if:
  ├─ Stop loss hit
  ├─ Take profit reached
  └─ Liquidation triggered
```

---

## Deployment Architecture

### Container Strategy

**Backend Container:**
- Base: `python:3.10-slim`
- Size: ~500MB
- Registry: GitHub Container Registry
- Multi-stage build for optimization

**Frontend Container:**
- Base: `node:18-alpine`
- Size: ~200MB
- Pre-built Next.js output
- Nginx reverse proxy

**Image Strategy:**
- Immutable tags (git SHA)
- Semantic versioning (v1.0.0)
- Build on every push
- Push to registry on main/develop

### Kubernetes Deployment

**Namespace:** `alphaforge`

**Backend Deployment:**
- 3 replicas (anti-affinity across AZs)
- Rolling updates (1 surge, 0 unavailable)
- Resource requests: 500m CPU, 512Mi memory
- Resource limits: 1000m CPU, 1Gi memory
- Liveness probe: /health/live (10s interval)
- Readiness probe: /health/ready (5s interval)
- Startup probe: /health/startup (30s max)

**Frontend Deployment:**
- 3 replicas (anti-affinity across AZs)
- Resource requests: 250m CPU, 256Mi memory
- Resource limits: 500m CPU, 512Mi memory
- Horizontal Pod Autoscaler (75% CPU, 80% memory)

**Ingress:**
- AWS ALB Ingress Controller
- TLS termination (AWS Certificate Manager)
- WAF rules (AWS WAF)
- Rate limiting (nginx)
- 2 DNS entries:
  - `alphaforge.example.com` → frontend
  - `api.alphaforge.example.com` → backend

### Auto-Scaling Strategy

**Horizontal Pod Autoscaler (HPA):**
```yaml
Backend:
  Min replicas: 3
  Max replicas: 10
  CPU threshold: 70%
  Memory threshold: 80%
  Scale-up cooldown: 60s
  Scale-down cooldown: 300s

Frontend:
  Min replicas: 3
  Max replicas: 8
  CPU threshold: 75%
  Memory threshold: 80%
```

**Cluster Autoscaler:**
- Min nodes: 2
- Max nodes: 10
- Target utilization: 70%

---

## Data Storage Strategy

### Database (PostgreSQL RDS)

**Configuration:**
- Engine: PostgreSQL 15
- Instance: db.t3.medium (production: db.r5.xlarge)
- Storage: 100GB SSD (gp3), auto-scaling
- Multi-AZ: Yes (production)
- Backup: 30-day retention
- Encryption: AES-256 at rest

**Performance Optimizations:**
- Connection pooling (pgBouncer)
- Query indexes for critical paths
- Materialized views for complex aggregations
- Partitioning for large tables (>10M rows)
- Read replicas for analytics workload

**Row-Level Security (RLS):**
```sql
-- Users can only see their own data
CREATE POLICY user_isolation ON portfolios
  USING (user_id = current_user_id());
```

### Cache (Redis ElastiCache)

**Configuration:**
- Engine: Redis 7
- Node type: cache.t3.micro (development), cache.r6g.large (production)
- Num nodes: 3 (production)
- Automatic failover: Yes
- Encryption: TLS for transport, at-rest encryption

**Cache Strategy:**
```
Market data cache:        TTL 5 seconds
Signal rankings:          TTL 1 minute
Portfolio summaries:      TTL 10 seconds
User settings:            TTL 1 hour
API responses:            TTL 5 minutes
Session data:             TTL 24 hours
```

**Cache Eviction:** LRU with memory limit 256MB

### Object Storage (S3)

**Buckets:**
- Trading data exports
- Strategy backtest results
- User documentation
- Audit logs

**Configuration:**
- Encryption: AES-256
- Versioning: Enabled
- Lifecycle: Archive to Glacier after 90 days
- Access: Private (CloudFront CDN in front)

---

## Monitoring & Observability

### Metrics (Prometheus)

**Scraped endpoints:**
- Backend: `:8001/metrics` (Prometheus client)
- Frontend: `:3000/metrics` (OpenTelemetry)
- Infrastructure: Node exporter, cAdvisor

**Key metrics:**
```
Backend:
  - http_request_duration_seconds
  - http_requests_total
  - database_query_duration_seconds
  - paper_trade_execution_latency
  - portfolio_update_latency

Frontend:
  - page_load_time_seconds
  - api_response_time_seconds
  - websocket_message_latency
  - user_interaction_time
```

### Logging (ELK Stack)

**Log sources:**
- Application logs (stdout/stderr)
- Database slow query logs
- Nginx access logs
- Audit logs (compliance)

**Log retention:** 30 days (searchable), 1 year (S3 archive)

**Alerting:**
- High error rate (>5% 5xx)
- Slow queries (>1s)
- Failed trades (manual review)
- Authentication failures
- Database connection pool exhaustion

### Tracing (Jaeger)

**Instrumentation:**
- All API endpoints
- Database queries
- External API calls
- WebSocket connections

**Sampling:** 10% in production, 100% in development

### Health Checks

**Liveness Probe:** `/health/live`
```json
{
  "status": "alive",
  "uptime_seconds": 123456
}
```

**Readiness Probe:** `/health/ready`
```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected",
  "kafka": "connected"
}
```

**Startup Probe:** `/health/startup`
```json
{
  "status": "ready",
  "migrations": "completed",
  "services": "initialized"
}
```

---

## Security Architecture

### Authentication & Authorization

**Auth Flow:**
1. User signs in with Firebase
2. Firebase returns ID token
3. Frontend sends token in `Authorization: Bearer <token>` header
4. Backend verifies token using Firebase Admin SDK
5. Token payload includes user UID
6. UID used for all authorization checks

**Authorization:**
- Row-level security (RLS) in database
- API endpoint checks: user_id == firebase_uid
- Admin operations require special role
- Sensitive operations logged for compliance

### Data Protection

**In Transit:**
- All traffic over HTTPS/TLS 1.3
- WebSocket over WSS (TLS)
- Certificate pinning for critical APIs

**At Rest:**
- Database: AES-256 encryption
- Redis: TLS + encryption
- S3: Server-side encryption
- Secrets: AWS Secrets Manager

**Key Management:**
- AWS KMS for key rotation
- Automatic key rotation (annual)
- Separate encryption keys per environment

### Network Security

**VPC:**
- Public subnets for ALB only
- Private subnets for EKS, RDS, Redis
- No direct internet access from database
- NAT Gateway for outbound traffic

**Security Groups:**
- Ingress: Only required ports
- Egress: Whitelist external APIs
- Internal: Allow pod-to-pod communication

**Network Policies (Kubernetes):**
- Deny all by default
- Explicit allow for required traffic
- Pod-to-pod isolation
- Egress to external only on specific ports

---

## Disaster Recovery & Business Continuity

### Backup Strategy

**Database:**
- Automated daily backups
- Point-in-time restore (last 30 days)
- Cross-region backup replication
- Test restore quarterly

**Configuration:**
- Infrastructure as Code (Terraform) in Git
- Kubernetes manifests in Git
- Secrets in AWS Secrets Manager

**RPO (Recovery Point Objective):** 1 hour
**RTO (Recovery Time Objective):** 4 hours

### Failover Procedures

**RDS Failover:**
- Automatic failover to standby (Multi-AZ)
- Failover time: <1 minute
- Application auto-reconnects

**Kubernetes Node Failure:**
- Pods automatically rescheduled
- Stateless application, no data loss
- PDB ensures minimum replicas

**Region Failover:**
- Manual DR activation
- Restore from cross-region backup
- Estimated RTO: 4 hours

---

## Performance Targets

| Metric | Target | SLO |
|--------|--------|-----|
| API Response (p99) | <2000ms | 99.5% |
| API Response (p95) | <1000ms | 99.5% |
| Portfolio Load | <500ms | 99% |
| Trade Execution | <1000ms | 99.9% |
| Page Load | <3000ms | 99% |
| WebSocket Latency | <500ms | 99.9% |
| Database Latency (p99) | <100ms | 99.9% |

---

## Cost Optimization

**Compute:**
- Reserved instances (30% savings)
- Spot instances for non-critical workloads (70% savings)
- Auto-scaling prevents over-provisioning

**Storage:**
- S3 lifecycle policies (60% savings)
- Database IOPS optimization
- Log rotation and archival

**Network:**
- CloudFront CDN (egress savings)
- VPC endpoints for AWS services
- NAT Gateway optimization

**Estimated Monthly Cost (Production):**
- Compute (EKS): $1,200
- Database (RDS): $400
- Cache (Redis): $150
- Storage (S3): $100
- Data transfer: $200
- **Total: ~$2,050/month** (for 1000 active users)

---

## Future Enhancements

1. **Multi-region deployment** for geo-redundancy
2. **GraphQL API** for flexible querying
3. **Mobile native app** (iOS/Android)
4. **Live trading** (not just paper trading)
5. **Advanced AI models** for signal generation
6. **Community features** (social trading)
7. **API for third-party integrations**
8. **Compliance certifications** (ISO 27001, SOC 2)

---

## Architecture Decision Records (ADRs)

### ADR-001: Why FastAPI instead of Django/Flask?

**Decision:** Use FastAPI for backend

**Rationale:**
- Native async/await support (essential for real-time updates)
- Automatic OpenAPI documentation
- Performance (faster than Flask, comparable to Node)
- Modern Python 3.7+ features
- Growing ecosystem and community

**Alternatives Considered:**
- Django: Too heavy, not async-first
- Flask: No native async support, slower
- Node.js: Type safety concerns
- Go: Language learning curve

### ADR-002: Why Kubernetes instead of traditional VMs?

**Decision:** Use EKS (managed Kubernetes)

**Rationale:**
- Auto-scaling matches trading load patterns
- Rolling updates with zero downtime
- Resource efficiency (90% vs 60% for VMs)
- Disaster recovery and YAML-as-config
- Cost savings with spot instances

### ADR-003: Why PostgreSQL for OLTP?

**Decision:** PostgreSQL for application data

**Rationale:**
- ACID guarantees for financial data
- Row-level security (RLS) for multi-tenancy
- JSON/JSONB for flexible schema
- Full-text search capability
- Good enough performance for most queries

**Complemented by:**
- ClickHouse for OLAP (analytics)
- Redis for caching and real-time state

---

**Document Version:** 1.0  
**Last Updated:** 2026-07-05  
**Next Review:** 2026-10-05
