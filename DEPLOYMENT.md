# AlphaForge Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Deployment Procedures](#deployment-procedures)
5. [Verification Steps](#verification-steps)
6. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Tools

```bash
# AWS CLI
aws --version  # >= 2.10.0

# Terraform
terraform --version  # >= 1.5.0

# kubectl
kubectl version --client  # >= 1.28.0

# Helm (optional, for package management)
helm version  # >= 3.12.0

# Docker (for local image building)
docker --version  # >= 24.0.0

# k6 (for load testing)
k6 version  # >= 0.45.0
```

### AWS Credentials Setup

```bash
# Configure AWS credentials
aws configure --profile alphaforge
# Enter: Access Key ID, Secret Access Key, Region, Output format

# Set environment variable
export AWS_PROFILE=alphaforge
```

### Environment Variables

Create `.env.production`:
```bash
# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Database
DB_USERNAME=alphaforge_admin
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=alphaforge

# Firebase
FIREBASE_PROJECT_ID=alphaforge-prod
FIREBASE_API_KEY=xxx

# Domains
FRONTEND_DOMAIN=alphaforge.example.com
API_DOMAIN=api.alphaforge.example.com
ALERT_EMAIL=ops@alphaforge.com
```

---

## Infrastructure Setup

### Step 1: Prepare AWS Account

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket alphaforge-terraform-state \
  --region us-east-1 \
  --acl private

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket alphaforge-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket alphaforge-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locks
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

### Step 2: Initialize Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Format and validate configuration
terraform fmt -recursive
terraform validate

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region           = "us-east-1"
environment          = "production"
db_username          = "alphaforge_admin"
db_password          = "$(openssl rand -base64 32)"
redis_num_nodes      = 3
alert_email          = "ops@alphaforge.com"
public_access_cidrs  = ["YOUR_IP/32"]  # Restrict to your IP
EOF

# Plan infrastructure
terraform plan -out=tfplan

# Review plan and apply
terraform apply tfplan
```

### Step 3: Configure kubectl Access

```bash
# Get cluster credentials
aws eks update-kubeconfig \
  --name alphaforge-production \
  --region us-east-1

# Verify connection
kubectl get nodes
kubectl get namespaces

# Create alphaforge namespace
kubectl create namespace alphaforge
```

### Step 4: Create Secrets

```bash
# Firebase service account
kubectl create secret generic firebase-key-secret \
  --from-file=/path/to/firebase-key.json \
  -n alphaforge

# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=username=alphaforge_admin \
  --from-literal=password="$(openssl rand -base64 32)" \
  -n alphaforge

# API keys
kubectl create secret generic api-keys \
  --from-literal=jwt_secret="$(openssl rand -base64 32)" \
  --from-literal=encryption_key="$(openssl rand -base64 32)" \
  -n alphaforge
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/ci.yml`

**Pipeline Stages:**
1. **Test** - Run tests, security scans
2. **Build** - Build Docker images
3. **Push** - Push to container registry
4. **Deploy** - Deploy to staging/production

### Triggering Deployments

```bash
# Automatic on push to main/develop
git push origin main

# Manual deployment
gh workflow run ci.yml -f environment=production

# Check workflow status
gh run list
gh run view <run_id> --log
```

### Container Registry

```bash
# Login to GitHub Container Registry
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin

# Build locally
docker build -f backend/Dockerfile -t ghcr.io/alphaforge/backend:latest .
docker push ghcr.io/alphaforge/backend:latest

# Verify image
docker pull ghcr.io/alphaforge/backend:latest
```

---

## Deployment Procedures

### Blue-Green Deployment

Blue-green deployment enables zero-downtime updates:

```bash
# Current production (Blue)
kubectl get deployment alphaforge-backend -n alphaforge

# Deploy new version (Green)
kubectl set image deployment/alphaforge-backend \
  backend=ghcr.io/alphaforge/backend:new-sha \
  -n alphaforge

# Monitor rollout
kubectl rollout status deployment/alphaforge-backend -n alphaforge

# Verify Green is healthy
kubectl logs -f deployment/alphaforge-backend -n alphaforge
```

### Rolling Update

```bash
# Update replicas with rolling strategy
kubectl patch deployment alphaforge-backend \
  -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":1,"maxUnavailable":1}}}}' \
  -n alphaforge

# Monitor progress
watch kubectl get pods -n alphaforge
```

### Canary Deployment

```bash
# Deploy 1 replica of new version
kubectl create deployment alphaforge-backend-canary \
  --image=ghcr.io/alphaforge/backend:new-sha \
  --replicas=1 \
  -n alphaforge

# Monitor canary metrics (5 minutes)
kubectl logs deployment/alphaforge-backend-canary -n alphaforge

# If healthy, roll out to all replicas
kubectl scale deployment alphaforge-backend --replicas=2 -n alphaforge
kubectl delete deployment alphaforge-backend-canary -n alphaforge
```

### Database Migrations

```bash
# Run migrations in job
kubectl apply -f - << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-$(date +%s)
  namespace: alphaforge
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: ghcr.io/alphaforge/backend:latest
        command: ["python", "-m", "alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: alphaforge-secrets
      restartPolicy: Never
EOF

# Monitor job
kubectl logs job/db-migration-<id> -n alphaforge
```

### Frontend Deployment

```bash
# Update frontend image
kubectl set image deployment/alphaforge-frontend \
  frontend=ghcr.io/alphaforge/frontend:new-sha \
  -n alphaforge

# Verify rollout
kubectl rollout status deployment/alphaforge-frontend -n alphaforge
```

---

## Verification Steps

### Health Checks

```bash
# Check cluster health
kubectl get nodes
kubectl get pods -n alphaforge
kubectl describe nodes

# Pod readiness
kubectl get pods -n alphaforge -o wide

# Service endpoints
kubectl get svc -n alphaforge
kubectl get ingress -n alphaforge
```

### API Verification

```bash
# Get backend service IP
BACKEND_IP=$(kubectl get svc alphaforge-backend -n alphaforge -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health checks
curl http://$BACKEND_IP:8000/health/live
curl http://$BACKEND_IP:8000/health/ready

# Sample API call
curl -H "Authorization: Bearer test-token" \
  http://$BACKEND_IP:8000/api/signals?limit=5
```

### Database Verification

```bash
# Get RDS endpoint
ENDPOINT=$(terraform output -raw rds_endpoint | cut -d: -f1)

# Connect via psql
psql -h $ENDPOINT -U alphaforge_admin -d alphaforge

# Check tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

# Verify data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM portfolios;
```

### Load Testing

```bash
# Run k6 load test
k6 run backend/tests/load_test.js \
  --vus 100 \
  --duration 5m \
  --out csv=results.csv

# Analyze results
k6 run backend/tests/load_test.js \
  --vus 1000 \
  --stage 2m:100 --stage 5m:500 --stage 10m:1000 \
  --stage 5m:500 --stage 2m:0
```

---

## Rollback Procedures

### Automatic Rollback

```bash
# If deployment fails, auto-rollback
kubectl rollout undo deployment/alphaforge-backend -n alphaforge

# Monitor rollback
kubectl rollout status deployment/alphaforge-backend -n alphaforge
```

### Manual Rollback

```bash
# Get rollout history
kubectl rollout history deployment/alphaforge-backend -n alphaforge

# Rollback to previous version
kubectl rollout undo deployment/alphaforge-backend -n alphaforge --to-revision=5

# Verify rollback
kubectl get pods -n alphaforge
kubectl logs deployment/alphaforge-backend -n alphaforge
```

### Database Rollback

```bash
# Downgrade database schema
kubectl exec -it <pod-name> -n alphaforge -- \
  python -m alembic downgrade -1

# Restore from RDS backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier alphaforge-restored \
  --db-snapshot-identifier alphaforge-snapshot-2026-07-05
```

---

## Monitoring Deployment

### Real-time Monitoring

```bash
# Watch pod events
kubectl get events -n alphaforge --sort-by='.lastTimestamp'

# Monitor resource usage
kubectl top nodes
kubectl top pods -n alphaforge

# Check logs
kubectl logs -f deployment/alphaforge-backend -n alphaforge

# Kubernetes dashboard
kubectl proxy
# Navigate to: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Prometheus Metrics

```bash
# Port-forward to Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Query metrics
curl http://localhost:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])
```

### Application Monitoring

```bash
# Check Sentry for errors
# https://sentry.io/organizations/alphaforge/

# Check application logs in CloudWatch
aws logs tail /aws/eks/alphaforge-production --follow

# Monitor RDS
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=alphaforge-production \
  --start-time 2026-07-05T00:00:00Z \
  --end-time 2026-07-06T00:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

---

## Post-Deployment Checklist

- [ ] All pods running (3+ replicas)
- [ ] No pending restarts or errors
- [ ] Health checks passing (live/ready)
- [ ] API responding to requests
- [ ] Database connected and migrated
- [ ] Redis cache functional
- [ ] Monitoring alerts configured
- [ ] Backups scheduled
- [ ] Logs being collected
- [ ] Metrics being scraped
- [ ] Smoke tests passing

---

## Emergency Procedures

### Degraded Performance

```bash
# Check resource usage
kubectl top pods -n alphaforge

# Scale up if needed
kubectl scale deployment alphaforge-backend --replicas=5 -n alphaforge

# Check for stuck pods
kubectl delete pod <stuck-pod> -n alphaforge

# Restart deployment
kubectl rollout restart deployment/alphaforge-backend -n alphaforge
```

### Database Issues

```bash
# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier alphaforge-production

# Reboot instance if needed
aws rds reboot-db-instance \
  --db-instance-identifier alphaforge-production

# Check connection pool
aws rds describe-db-clusters \
  --db-cluster-identifier alphaforge-production
```

### Complete Cluster Failure

```bash
# Verify state from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier alphaforge-restored \
  --db-snapshot-identifier alphaforge-latest-backup

# Redeploy from Terraform
cd infrastructure/terraform
terraform apply -auto-approve

# Redeploy applications
kubectl apply -f infrastructure/kubernetes/
```

---

**Version:** 1.0  
**Last Updated:** 2026-07-05  
**Maintained By:** DevOps Team
