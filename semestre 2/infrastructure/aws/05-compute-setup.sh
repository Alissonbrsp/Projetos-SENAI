#!/usr/bin/env bash
# =============================================================================
# Script 05: EC2 — Lançamento das 3 VMs
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail

source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"
source "$DEPLOYED"

echo "============================================"
echo " [05/07] Lançando instâncias EC2 (3 VMs)"
echo "============================================"

# ---------------------------------------------------------------------------
# VM1: Management (Ubuntu 22.04, t3.small)
# ---------------------------------------------------------------------------
echo "[EC2] Lançando VM1 (Management)..."
VM1_ID=$(aws ec2 run-instances \
  --image-id "$VM1_AMI" \
  --instance-type "$VM1_INSTANCE_TYPE" \
  --key-name "$KEY_PAIR_NAME" \
  --security-group-ids "$SG_VM1" \
  --subnet-id "$SUBNET_PUB_A" \
  --associate-public-ip-address \
  --tag-specifications \
    "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-vm1-management},{Key=Project,Value=${PROJECT_NAME}},{Key=Role,Value=management}]" \
  --user-data '#!/bin/bash
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv nginx postgresql redis-server
    echo "VM1 ready" > /tmp/vm1-ready.txt' \
  --query "Instances[0].InstanceId" --output text)

echo "[EC2] VM1 ID: $VM1_ID — Aguardando running..."
aws ec2 wait instance-running --instance-ids "$VM1_ID"

# Associar Elastic IP
aws ec2 associate-address --instance-id "$VM1_ID" --allocation-id "$EIP_VM1_ALLOC"
VM1_IP=$(aws ec2 describe-addresses --allocation-ids "$EIP_VM1_ALLOC" \
  --query "Addresses[0].PublicIp" --output text)
echo "[EC2] ✓ VM1 online: $VM1_IP"

# ---------------------------------------------------------------------------
# VM2: Broker (Ubuntu 22.04, t3.micro)
# ---------------------------------------------------------------------------
echo "[EC2] Lançando VM2 (Broker)..."
VM2_ID=$(aws ec2 run-instances \
  --image-id "$VM2_AMI" \
  --instance-type "$VM2_INSTANCE_TYPE" \
  --key-name "$KEY_PAIR_NAME" \
  --security-group-ids "$SG_VM2" \
  --subnet-id "$SUBNET_PUB_A" \
  --associate-public-ip-address \
  --tag-specifications \
    "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-vm2-broker},{Key=Project,Value=${PROJECT_NAME}},{Key=Role,Value=broker}]" \
  --user-data '#!/bin/bash
    apt-get update -y
    apt-get install -y mosquitto mosquitto-clients
    echo "VM2 ready" > /tmp/vm2-ready.txt' \
  --query "Instances[0].InstanceId" --output text)

aws ec2 wait instance-running --instance-ids "$VM2_ID"
aws ec2 associate-address --instance-id "$VM2_ID" --allocation-id "$EIP_VM2_ALLOC"
VM2_IP=$(aws ec2 describe-addresses --allocation-ids "$EIP_VM2_ALLOC" \
  --query "Addresses[0].PublicIp" --output text)
echo "[EC2] ✓ VM2 online: $VM2_IP"

# ---------------------------------------------------------------------------
# VM3: CTF Arena (Debian 12, t3.medium) — com User Data e Instance Profile
# ---------------------------------------------------------------------------
echo "[EC2] Lançando VM3 (CTF Arena)..."

# Codificar user-data em base64 (script completo está em vm3-ctf/user-data.sh)
USER_DATA=$(base64 -w0 "$(dirname "$0")/../../vm3-ctf/user-data.sh")

VM3_ID=$(aws ec2 run-instances \
  --image-id "$VM3_AMI" \
  --instance-type "$VM3_INSTANCE_TYPE" \
  --key-name "$KEY_PAIR_NAME" \
  --security-group-ids "$SG_VM3" \
  --subnet-id "$SUBNET_PUB_A" \
  --iam-instance-profile "Name=${PROJECT_NAME}-EC2-CTF-Instance-Profile" \
  --metadata-options "HttpTokens=optional,HttpEndpoint=enabled" \
  --associate-public-ip-address \
  --user-data "$USER_DATA" \
  --tag-specifications \
    "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-vm3-ctf},{Key=Project,Value=${PROJECT_NAME}},{Key=Role,Value=ctf-arena}]" \
  --query "Instances[0].InstanceId" --output text)

aws ec2 wait instance-running --instance-ids "$VM3_ID"
aws ec2 associate-address --instance-id "$VM3_ID" --allocation-id "$EIP_VM3_ALLOC"
VM3_IP=$(aws ec2 describe-addresses --allocation-ids "$EIP_VM3_ALLOC" \
  --query "Addresses[0].PublicIp" --output text)
echo "[EC2] ✓ VM3 online: $VM3_IP"

# ---------------------------------------------------------------------------
# Salvar IDs e IPs
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
VM1_INSTANCE_ID=$VM1_ID
VM2_INSTANCE_ID=$VM2_ID
VM3_INSTANCE_ID=$VM3_ID
VM1_IP=$VM1_IP
VM2_IP=$VM2_IP
VM3_IP=$VM3_IP
EOF

echo ""
echo "✅ [05/07] VMs lançadas com sucesso!"
echo "   VM1 (Management) : $VM1_IP"
echo "   VM2 (Broker)     : $VM2_IP"
echo "   VM3 (CTF Arena)  : $VM3_IP"
echo ""
echo "   Próximo passo: execute o setup de cada VM via SSH"
echo "   ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@$VM1_IP"
