#!/usr/bin/env bash
# =============================================================================
# Script 02: VPC, Subnets, Security Groups, Elastic IPs
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail

source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"

echo "================================================"
echo " [02/07] Configurando Rede: VPC e Security Groups"
echo "================================================"

# ---------------------------------------------------------------------------
# 1. VPC
# ---------------------------------------------------------------------------
echo "[NET] Criando VPC 10.0.0.0/16..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block "10.0.0.0/16" \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc},{Key=Project,Value=${PROJECT_NAME}}]" \
  --query "Vpc.VpcId" --output text)

aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-support

echo "[NET] VPC criada: $VPC_ID"

# ---------------------------------------------------------------------------
# 2. Internet Gateway
# ---------------------------------------------------------------------------
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw}]" \
  --query "InternetGateway.InternetGatewayId" --output text)
aws ec2 attach-internet-gateway --vpc-id "$VPC_ID" --internet-gateway-id "$IGW_ID"

# ---------------------------------------------------------------------------
# 3. Subnets
# ---------------------------------------------------------------------------
echo "[NET] Criando subnets..."

SUBNET_PUB_A=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block "10.0.1.0/24" \
  --availability-zone "${AWS_REGION}a" \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-pub-a}]" \
  --query "Subnet.SubnetId" --output text)

SUBNET_PUB_B=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block "10.0.2.0/24" \
  --availability-zone "${AWS_REGION}b" \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-pub-b}]" \
  --query "Subnet.SubnetId" --output text)

SUBNET_PRIV=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block "10.0.10.0/24" \
  --availability-zone "${AWS_REGION}a" \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-priv-a}]" \
  --query "Subnet.SubnetId" --output text)

# Route table pública
RT_PUB=$(aws ec2 create-route-table \
  --vpc-id "$VPC_ID" \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-rt-pub}]" \
  --query "RouteTable.RouteTableId" --output text)

aws ec2 create-route --route-table-id "$RT_PUB" \
  --destination-cidr-block "0.0.0.0/0" --gateway-id "$IGW_ID"

aws ec2 associate-route-table --route-table-id "$RT_PUB" --subnet-id "$SUBNET_PUB_A"
aws ec2 associate-route-table --route-table-id "$RT_PUB" --subnet-id "$SUBNET_PUB_B"

# ---------------------------------------------------------------------------
# 4. Security Groups
# ---------------------------------------------------------------------------
echo "[NET] Criando Security Groups..."

tag_sg() {
  aws ec2 create-tags --resources "$1" \
    --tags "Key=Name,Value=$2" "Key=Project,Value=${PROJECT_NAME}"
}

# SG: ALB
SG_ALB=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-ALB" \
  --description "SG do Application Load Balancer" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_ALB" "${PROJECT_NAME}-SG-ALB"
aws ec2 authorize-security-group-ingress --group-id "$SG_ALB" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTP}]" \
  "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTPS}]"

# SG: VM1 Management
SG_VM1=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-VM1" \
  --description "SG da VM1 (Management)" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_VM1" "${PROJECT_NAME}-SG-VM1"
aws ec2 authorize-security-group-ingress --group-id "$SG_VM1" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=80,ToPort=80,UserIdGroupPairs=[{GroupId=${SG_ALB},Description=Nginx via ALB}]" \
  "IpProtocol=tcp,FromPort=8000,ToPort=8000,UserIdGroupPairs=[{GroupId=${SG_ALB},Description=FastAPI via ALB}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${ADMIN_IP},Description=SSH Admin}]"

# SG: VM2 Broker
SG_VM2=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-VM2" \
  --description "SG da VM2 (Broker MQTT)" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_VM2" "${PROJECT_NAME}-SG-VM2"
aws ec2 authorize-security-group-ingress --group-id "$SG_VM2" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=1883,ToPort=1883,IpRanges=[{CidrIp=0.0.0.0/0,Description=MQTT}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${ADMIN_IP},Description=SSH Admin}]"

# SG: VM3 CTF Arena
SG_VM3=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-VM3" \
  --description "SG da VM3 (CTF Arena)" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_VM3" "${PROJECT_NAME}-SG-VM3"
aws ec2 authorize-security-group-ingress --group-id "$SG_VM3" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description=Grafana}]" \
  "IpProtocol=tcp,FromPort=5000,ToPort=5000,IpRanges=[{CidrIp=0.0.0.0/0,Description=Vulnerable API}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${ADMIN_IP},Description=SSH Admin}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,UserIdGroupPairs=[{GroupId=${SG_VM1},Description=Reset remoto VM1}]"

# SG: RDS
SG_RDS=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-RDS" \
  --description "SG do RDS PostgreSQL" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_RDS" "${PROJECT_NAME}-SG-RDS"
aws ec2 authorize-security-group-ingress --group-id "$SG_RDS" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=${SG_VM1},Description=VM1 backend}]"

# SG: ElastiCache
SG_REDIS=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-SG-Redis" \
  --description "SG do ElastiCache Redis" \
  --vpc-id "$VPC_ID" --query "GroupId" --output text)
tag_sg "$SG_REDIS" "${PROJECT_NAME}-SG-Redis"
aws ec2 authorize-security-group-ingress --group-id "$SG_REDIS" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=6379,ToPort=6379,UserIdGroupPairs=[{GroupId=${SG_VM1},Description=VM1 backend}]"

# ---------------------------------------------------------------------------
# 5. Elastic IPs
# ---------------------------------------------------------------------------
echo "[NET] Alocando Elastic IPs..."
EIP_VM1=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-eip-vm1}]" \
  --query "AllocationId" --output text)
EIP_VM2=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-eip-vm2}]" \
  --query "AllocationId" --output text)
EIP_VM3=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-eip-vm3}]" \
  --query "AllocationId" --output text)

# ---------------------------------------------------------------------------
# 6. Salvar IDs para scripts posteriores
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
VPC_ID=$VPC_ID
SUBNET_PUB_A=$SUBNET_PUB_A
SUBNET_PUB_B=$SUBNET_PUB_B
SUBNET_PRIV=$SUBNET_PRIV
SG_ALB=$SG_ALB
SG_VM1=$SG_VM1
SG_VM2=$SG_VM2
SG_VM3=$SG_VM3
SG_RDS=$SG_RDS
SG_REDIS=$SG_REDIS
EIP_VM1_ALLOC=$EIP_VM1
EIP_VM2_ALLOC=$EIP_VM2
EIP_VM3_ALLOC=$EIP_VM3
EOF

echo ""
echo "✅ [02/07] Rede configurada com sucesso!"
echo "   VPC: $VPC_ID | Subnets: $SUBNET_PUB_A, $SUBNET_PUB_B, $SUBNET_PRIV"
echo "   Security Groups criados: SG-ALB, SG-VM1, SG-VM2, SG-VM3, SG-RDS, SG-Redis"
