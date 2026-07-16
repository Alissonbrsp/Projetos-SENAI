#!/usr/bin/env bash
# =============================================================================
# Script 04: RDS PostgreSQL + ElastiCache Redis
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"
source "$DEPLOYED"

echo "================================================"
echo " [04/07] Provisionando RDS + ElastiCache"
echo "================================================"

# ---------------------------------------------------------------------------
# Subnet Group (necessário para RDS e ElastiCache na subnet privada)
# ---------------------------------------------------------------------------
aws rds create-db-subnet-group \
  --db-subnet-group-name "${PROJECT_NAME}-db-subnet" \
  --db-subnet-group-description "Subnet group CTF IIoT" \
  --subnet-ids "$SUBNET_PRIV" "$SUBNET_PUB_B" \
  --tags "Key=Project,Value=${PROJECT_NAME}"

aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name "${PROJECT_NAME}-redis-subnet" \
  --cache-subnet-group-description "Redis subnet CTF IIoT" \
  --subnet-ids "$SUBNET_PRIV" "$SUBNET_PUB_B"

# ---------------------------------------------------------------------------
# RDS PostgreSQL (db.t3.micro, single-AZ)
# ---------------------------------------------------------------------------
echo "[DB] Criando RDS PostgreSQL (leva ~10 min)..."
aws rds create-db-instance \
  --db-instance-identifier "${PROJECT_NAME}-postgres" \
  --db-instance-class "$DB_INSTANCE_TYPE" \
  --engine postgres \
  --engine-version "15.4" \
  --master-username "$DB_USER" \
  --master-user-password "$DB_PASSWORD" \
  --db-name "$DB_NAME" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --no-publicly-accessible \
  --vpc-security-group-ids "$SG_RDS" \
  --db-subnet-group-name "${PROJECT_NAME}-db-subnet" \
  --backup-retention-period 7 \
  --no-multi-az \
  --tags "Key=Project,Value=${PROJECT_NAME}"

echo "[DB] Aguardando RDS ficar disponível..."
aws rds wait db-instance-available \
  --db-instance-identifier "${PROJECT_NAME}-postgres"

RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier "${PROJECT_NAME}-postgres" \
  --query "DBInstances[0].Endpoint.Address" --output text)
echo "[DB] ✓ RDS disponível: $RDS_ENDPOINT"

# ---------------------------------------------------------------------------
# ElastiCache Redis (cache.t3.micro, single-node)
# ---------------------------------------------------------------------------
echo "[CACHE] Criando ElastiCache Redis..."
aws elasticache create-cache-cluster \
  --cache-cluster-id "${PROJECT_NAME}-redis" \
  --cache-node-type "$REDIS_NODE_TYPE" \
  --engine redis \
  --engine-version "7.0" \
  --num-cache-nodes 1 \
  --cache-subnet-group-name "${PROJECT_NAME}-redis-subnet" \
  --security-group-ids "$SG_REDIS" \
  --tags "Key=Project,Value=${PROJECT_NAME}"

echo "[CACHE] Aguardando Redis ficar disponível..."
aws elasticache wait cache-cluster-available \
  --cache-cluster-id "${PROJECT_NAME}-redis"

REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id "${PROJECT_NAME}-redis" \
  --show-cache-node-info \
  --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text)
echo "[CACHE] ✓ Redis disponível: $REDIS_ENDPOINT"

# ---------------------------------------------------------------------------
# Salvar endpoints
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
RDS_ENDPOINT=$RDS_ENDPOINT
REDIS_ENDPOINT=$REDIS_ENDPOINT
EOF

echo ""
echo "✅ [04/07] Banco de dados provisionados!"
echo "   RDS   : $RDS_ENDPOINT:5432"
echo "   Redis : $REDIS_ENDPOINT:6379"
