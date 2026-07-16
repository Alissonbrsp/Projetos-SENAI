#!/usr/bin/env bash
# =============================================================================
# Script 01: IAM Roles e Políticas
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail

source "$(dirname "$0")/.env"

echo "==========================================="
echo " [01/07] Configurando IAM Roles e Políticas"
echo "==========================================="

# ---------------------------------------------------------------------------
# 1. Policy: Lambda EC2 Manager
#    Permite que a Lambda ligue/desligue/verifique apenas a VM3
# ---------------------------------------------------------------------------
echo "[IAM] Criando política Lambda-EC2-Manager..."

aws iam create-policy \
  --policy-name "${PROJECT_NAME}-Lambda-EC2-Manager" \
  --description "Permite que a Lambda gerencie o ciclo de vida da VM3 (CTF Arena)" \
  --policy-document file://iam/lambda-ec2-manager-policy.json \
  --tags "Key=Project,Value=${PROJECT_NAME}"

# ---------------------------------------------------------------------------
# 2. Trust Policy: Lambda pode assumir esta role
# ---------------------------------------------------------------------------
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

echo "[IAM] Criando role Lambda-EC2-Manager-Role..."
aws iam create-role \
  --role-name "${PROJECT_NAME}-Lambda-EC2-Manager-Role" \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --description "Role para a Lambda gerenciar o ciclo de vida da VM3" \
  --tags "Key=Project,Value=${PROJECT_NAME}"

# Associar a policy à role
LAMBDA_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-Lambda-EC2-Manager"
aws iam attach-role-policy \
  --role-name "${PROJECT_NAME}-Lambda-EC2-Manager-Role" \
  --policy-arn "$LAMBDA_POLICY_ARN"

# Adicionar policy de logs CloudWatch para a Lambda
aws iam attach-role-policy \
  --role-name "${PROJECT_NAME}-Lambda-EC2-Manager-Role" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

echo "[IAM] ✓ Role Lambda-EC2-Manager-Role criada."

# ---------------------------------------------------------------------------
# 3. Instance Profile: EC2 CTF Arena (VM3)
#    Role associada à instância EC2 da VM3 — usado no cenário da Flag 2
#    Tem permissões mínimas (apenas leitura de tags próprias)
# ---------------------------------------------------------------------------
echo "[IAM] Criando política EC2-CTF-Instance..."

aws iam create-policy \
  --policy-name "${PROJECT_NAME}-EC2-CTF-Instance" \
  --description "Permissões mínimas para a instância EC2 da VM3" \
  --policy-document file://iam/ec2-ctf-instance-policy.json \
  --tags "Key=Project,Value=${PROJECT_NAME}"

cat > /tmp/ec2-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

echo "[IAM] Criando role EC2-CTF-Instance-Role..."
aws iam create-role \
  --role-name "${PROJECT_NAME}-EC2-CTF-Instance-Role" \
  --assume-role-policy-document file:///tmp/ec2-trust-policy.json \
  --description "Role da instância EC2 VM3 (CTF Arena)" \
  --tags "Key=Project,Value=${PROJECT_NAME}"

EC2_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-EC2-CTF-Instance"
aws iam attach-role-policy \
  --role-name "${PROJECT_NAME}-EC2-CTF-Instance-Role" \
  --policy-arn "$EC2_POLICY_ARN"

# Criar Instance Profile
aws iam create-instance-profile \
  --instance-profile-name "${PROJECT_NAME}-EC2-CTF-Instance-Profile"

aws iam add-role-to-instance-profile \
  --instance-profile-name "${PROJECT_NAME}-EC2-CTF-Instance-Profile" \
  --role-name "${PROJECT_NAME}-EC2-CTF-Instance-Role"

echo "[IAM] ✓ Instance Profile EC2-CTF criado."

# ---------------------------------------------------------------------------
# 4. Salvar ARNs para scripts posteriores
# ---------------------------------------------------------------------------
cat >> "$(dirname "$0")/.deployed-ips" << EOF
LAMBDA_ROLE_ARN=arn:aws:iam::${AWS_ACCOUNT_ID}:role/${PROJECT_NAME}-Lambda-EC2-Manager-Role
EC2_INSTANCE_PROFILE=${PROJECT_NAME}-EC2-CTF-Instance-Profile
EOF

echo ""
echo "✅ [01/07] IAM configurado com sucesso!"
echo "   → Role Lambda : ${PROJECT_NAME}-Lambda-EC2-Manager-Role"
echo "   → Instance Profile : ${PROJECT_NAME}-EC2-CTF-Instance-Profile"
