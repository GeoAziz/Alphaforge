terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  backend "s3" {
    bucket         = "alphaforge-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "alphaforge"
      ManagedBy   = "terraform"
    }
  }
}

provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}

# ============================================================================
# VPC & NETWORKING
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "alphaforge-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "alphaforge-private-subnet-${count.index + 1}"
    Type = "Private"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "alphaforge-public-subnet-${count.index + 1}"
    Type = "Public"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "alphaforge-igw"
  }
}

resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"

  depends_on = [aws_internet_gateway.main]

  tags = {
    Name = "alphaforge-nat-eip-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [aws_internet_gateway.main]

  tags = {
    Name = "alphaforge-nat-${count.index + 1}"
  }
}

# ============================================================================
# EKS CLUSTER
# ============================================================================

resource "aws_eks_cluster" "main" {
  name            = "alphaforge-${var.environment}"
  role_arn        = aws_iam_role.eks_cluster.arn
  version         = var.kubernetes_version
  ip_prefix_count = 8

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.public_access_cidrs
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  tags = {
    Name = "alphaforge-eks"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller
  ]
}

data "aws_eks_cluster_auth" "main" {
  name = aws_eks_cluster.main.name
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "alphaforge-${var.environment}"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.private[*].id
  version         = var.kubernetes_version

  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
    min_size     = var.node_min_size
  }

  instance_types = var.node_instance_types

  update_config {
    max_unavailable_percentage = 33
  }

  tags = {
    Name = "alphaforge-node-group"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy
  ]
}

# ============================================================================
# RDS DATABASE
# ============================================================================

resource "aws_rds_subnet_group" "main" {
  name       = "alphaforge-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "alphaforge-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name   = "alphaforge-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "alphaforge-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "alphaforge-${var.environment}"
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_iops      = 3000
  storage_throughput = 125

  db_name  = "alphaforge"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_rds_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  multi_az                    = var.db_multi_az
  publicly_accessible         = false
  auto_minor_version_upgrade  = true
  deletion_protection         = var.db_deletion_protection
  copy_tags_to_snapshot       = true
  skip_final_snapshot         = !var.environment == "production"
  final_snapshot_identifier   = "alphaforge-${var.environment}-final"
  enable_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "alphaforge-db"
  }
}

# ============================================================================
# REDIS CLUSTER
# ============================================================================

resource "aws_elasticache_subnet_group" "main" {
  name       = "alphaforge-redis-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "redis" {
  name   = "alphaforge-redis-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "alphaforge-redis-sg"
  }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "alphaforge-${var.environment}"
  engine               = "redis"
  node_type           = var.redis_node_type
  num_cache_nodes     = var.redis_num_nodes
  parameter_group_name = "default.redis7"
  engine_version      = "7.0"
  port                = 6379

  az_mode                   = var.redis_num_nodes > 1 ? "cross-az" : "single-az"
  subnet_group_name         = aws_elasticache_subnet_group.main.name
  security_group_ids        = [aws_security_group.redis.id]
  automatic_failover_enabled = var.redis_num_nodes > 1

  maintenance_window       = "sun:05:00-sun:07:00"
  notification_topic_arn   = aws_sns_topic.alerts.arn

  tags = {
    Name = "alphaforge-redis"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }
}

# ============================================================================
# S3 BUCKETS
# ============================================================================

resource "aws_s3_bucket" "trading_data" {
  bucket = "alphaforge-trading-data-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "alphaforge-trading-data"
  }
}

resource "aws_s3_bucket_versioning" "trading_data" {
  bucket = aws_s3_bucket.trading_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "trading_data" {
  bucket = aws_s3_bucket.trading_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/alphaforge-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "alphaforge-eks-logs"
  }
}

resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/alphaforge-${var.environment}/slow-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "alphaforge-redis-slow-logs"
  }
}

resource "aws_sns_topic" "alerts" {
  name = "alphaforge-${var.environment}-alerts"

  tags = {
    Name = "alphaforge-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "EKS cluster endpoint"
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "EKS cluster name"
}

output "rds_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "RDS database endpoint"
  sensitive   = true
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
  description = "Redis cluster endpoint"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.trading_data.bucket
  description = "S3 bucket for trading data"
}
