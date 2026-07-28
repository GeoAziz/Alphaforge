#!/bin/bash
set -euo pipefail

# AlphaForge Automated Deployment Script
# Usage: ./scripts/deploy.sh [environment] [region]

ENVIRONMENT="${1:-production}"
REGION="${2:-us-east-1}"
PROJECT="alphaforge"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN${NC} $1"
}

error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR${NC} $1"
  exit 1
}

# Check prerequisites
check_prerequisites() {
  log "Checking prerequisites..."

  for cmd in aws terraform kubectl docker; do
    if ! command -v $cmd &> /dev/null; then
      error "$cmd is not installed"
    fi
  done

  # Check AWS credentials
  if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    error "AWS credentials not configured"
  fi

  log "All prerequisites satisfied ✓"
}

# Setup AWS account
setup_aws() {
  log "Setting up AWS infrastructure..."

  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  BUCKET_NAME="$PROJECT-terraform-state-$ACCOUNT_ID"

  # Create S3 bucket for state
  if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    log "Creating S3 bucket for Terraform state: $BUCKET_NAME"
    aws s3api create-bucket \
      --bucket "$BUCKET_NAME" \
      --region "$REGION" \
      $([ "$REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$REGION" || true)

    aws s3api put-bucket-versioning \
      --bucket "$BUCKET_NAME" \
      --versioning-configuration Status=Enabled

    aws s3api put-bucket-encryption \
      --bucket "$BUCKET_NAME" \
      --server-side-encryption-configuration '{
        "Rules": [{
          "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
        }]
      }'
  fi

  # Create DynamoDB table for locks
  TABLE_NAME="$PROJECT-terraform-locks"
  if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" 2>/dev/null; then
    log "Creating DynamoDB table for state locks: $TABLE_NAME"
    aws dynamodb create-table \
      --table-name "$TABLE_NAME" \
      --attribute-definitions AttributeName=LockID,AttributeType=S \
      --key-schema AttributeName=LockID,KeyType=HASH \
      --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
      --region "$REGION"
  fi

  log "AWS infrastructure setup complete ✓"
}

# Initialize Terraform
terraform_init() {
  log "Initializing Terraform..."

  cd infrastructure/terraform

  terraform init \
    -backend-config="bucket=$BUCKET_NAME" \
    -backend-config="key=$ENVIRONMENT/terraform.tfstate" \
    -backend-config="region=$REGION" \
    -backend-config="dynamodb_table=$TABLE_NAME" \
    -backend-config="encrypt=true"

  terraform fmt -recursive
  terraform validate

  cd ../..
  log "Terraform initialization complete ✓"
}

# Plan Terraform
terraform_plan() {
  log "Planning Terraform changes..."

  cd infrastructure/terraform

  terraform plan \
    -var-file="environments/$ENVIRONMENT.tfvars" \
    -var="aws_region=$REGION" \
    -out="tfplan"

  cd ../..
  log "Terraform plan created: tfplan"
}

# Apply Terraform
terraform_apply() {
  log "Applying Terraform changes..."

  read -p "Continue with infrastructure deployment? (yes/no) " -r
  if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    error "Deployment cancelled"
  fi

  cd infrastructure/terraform

  terraform apply tfplan

  # Get outputs
  CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
  CLUSTER_ENDPOINT=$(terraform output -raw eks_cluster_endpoint)
  RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
  REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)

  cd ../..

  log "Infrastructure deployed ✓"
  log "Cluster: $CLUSTER_NAME"
  log "RDS: $RDS_ENDPOINT"
  log "Redis: $REDIS_ENDPOINT"
}

# Configure kubectl
configure_kubectl() {
  log "Configuring kubectl..."

  CLUSTER_NAME=$(cd infrastructure/terraform && terraform output -raw eks_cluster_name && cd ../..)

  aws eks update-kubeconfig \
    --name "$CLUSTER_NAME" \
    --region "$REGION"

  # Verify connection
  if kubectl cluster-info &> /dev/null; then
    log "kubectl configured successfully ✓"
  else
    error "Failed to configure kubectl"
  fi
}

# Create namespaces and secrets
setup_kubernetes() {
  log "Setting up Kubernetes..."

  # Create namespace
  kubectl create namespace $PROJECT 2>/dev/null || true

  # Create secrets
  log "Creating secrets..."

  # Database credentials
  DB_PASSWORD=$(openssl rand -base64 32)
  kubectl create secret generic db-credentials \
    --from-literal=username="alphaforge_admin" \
    --from-literal=password="$DB_PASSWORD" \
    -n $PROJECT \
    --dry-run=client -o yaml | kubectl apply -f -

  # API keys
  JWT_SECRET=$(openssl rand -base64 32)
  kubectl create secret generic api-keys \
    --from-literal=jwt_secret="$JWT_SECRET" \
    --from-literal=encryption_key="$(openssl rand -base64 32)" \
    -n $PROJECT \
    --dry-run=client -o yaml | kubectl apply -f -

  # Firebase key (if exists)
  if [ -f "$HOME/.config/alphaforge/firebase-key.json" ]; then
    kubectl create secret generic firebase-key-secret \
      --from-file="$HOME/.config/alphaforge/firebase-key.json" \
      -n $PROJECT \
      --dry-run=client -o yaml | kubectl apply -f -
  fi

  log "Kubernetes setup complete ✓"
}

# Build and push images
build_images() {
  log "Building Docker images..."

  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

  # Create ECR repositories if they don't exist
  for repo in backend frontend; do
    aws ecr describe-repositories \
      --repository-names "$PROJECT-$repo" \
      --region "$REGION" 2>/dev/null || \
    aws ecr create-repository \
      --repository-name "$PROJECT-$repo" \
      --region "$REGION"
  done

  # Login to ECR
  aws ecr get-login-password --region "$REGION" | \
    docker login --username AWS --password-stdin "$REGISTRY"

  # Build backend
  log "Building backend image..."
  docker build -f backend/Dockerfile -t "$REGISTRY/$PROJECT-backend:latest" .
  docker push "$REGISTRY/$PROJECT-backend:latest"

  # Build frontend
  log "Building frontend image..."
  docker build -f Dockerfile -t "$REGISTRY/$PROJECT-frontend:latest" .
  docker push "$REGISTRY/$PROJECT-frontend:latest"

  log "Docker images built and pushed ✓"
}

# Deploy applications
deploy_applications() {
  log "Deploying applications to Kubernetes..."

  # Update image references
  sed -i "s|ghcr.io/alphaforge/backend|$REGISTRY/$PROJECT-backend|g" infrastructure/kubernetes/backend-deployment.yaml
  sed -i "s|ghcr.io/alphaforge/frontend|$REGISTRY/$PROJECT-frontend|g" infrastructure/kubernetes/frontend-deployment.yaml

  # Apply manifests
  kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
  kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
  kubectl apply -f infrastructure/kubernetes/monitoring.yaml

  log "Waiting for deployments to be ready..."
  kubectl rollout status deployment/alphaforge-backend -n alphaforge --timeout=10m
  kubectl rollout status deployment/alphaforge-frontend -n alphaforge --timeout=10m

  log "Applications deployed ✓"
}

# Run verification tests
verify_deployment() {
  log "Running verification tests..."

  # Get service endpoints
  BACKEND_IP=$(kubectl get svc alphaforge-backend -n alphaforge -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")

  # Wait for LB to be assigned
  while [ "$BACKEND_IP" = "pending" ] || [ -z "$BACKEND_IP" ]; do
    warn "Waiting for load balancer IP..."
    sleep 10
    BACKEND_IP=$(kubectl get svc alphaforge-backend -n alphaforge -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
  done

  # Test API health
  log "Testing API health..."
  for i in {1..30}; do
    if curl -f -s "http://$BACKEND_IP:8000/health/ready" &> /dev/null; then
      log "API health check passed ✓"
      break
    fi
    warn "Attempt $i/30: Waiting for API to be ready..."
    sleep 10
  done

  log "Deployment verification complete ✓"
}

# Main execution
main() {
  log "===== AlphaForge Deployment ====="
  log "Environment: $ENVIRONMENT"
  log "Region: $REGION"
  log ""

  check_prerequisites
  setup_aws
  terraform_init
  terraform_plan
  terraform_apply
  configure_kubectl
  setup_kubernetes
  build_images
  deploy_applications
  verify_deployment

  log ""
  log "===== Deployment Complete ====="
  log "Frontend: https://alphaforge.example.com"
  log "API: https://api.alphaforge.example.com"
  log "Monitoring: https://grafana.alphaforge.internal"
  log ""
  log "Next steps:"
  log "  1. Update DNS records to point to load balancer"
  log "  2. Configure SSL certificates"
  log "  3. Set up monitoring alerts"
  log "  4. Run load tests: k6 run backend/tests/load_test.js"
  log "  5. Monitor logs: kubectl logs -f deployment/alphaforge-backend -n alphaforge"
}

main "$@"
