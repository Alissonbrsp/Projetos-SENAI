#!/usr/bin/env bash
# =============================================================================
# Script 07: ALB + AWS WAF (proteção DDoS / rate limiting)
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"
source "$DEPLOYED"

echo "======================================="
echo " [07/07] ALB + AWS WAF"
echo "======================================="

# ---------------------------------------------------------------------------
# 1. Application Load Balancer
# ---------------------------------------------------------------------------
echo "[ALB] Criando Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name "${PROJECT_NAME}-alb" \
  --type application \
  --scheme internet-facing \
  --ip-address-type ipv4 \
  --subnets "$SUBNET_PUB_A" "$SUBNET_PUB_B" \
  --security-groups "$SG_ALB" \
  --tags "Key=Project,Value=${PROJECT_NAME}" \
  --query "LoadBalancers[0].LoadBalancerArn" --output text)

ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns "$ALB_ARN" \
  --query "LoadBalancers[0].DNSName" --output text)

# Target Group → VM1
TG_ARN=$(aws elbv2 create-target-group \
  --name "${PROJECT_NAME}-tg-vm1" \
  --protocol HTTP --port 8000 \
  --vpc-id "$VPC_ID" \
  --health-check-path "/api/health" \
  --health-check-interval-seconds 30 \
  --query "TargetGroups[0].TargetGroupArn" --output text)

# Registrar VM1 no Target Group
aws elbv2 register-targets \
  --target-group-arn "$TG_ARN" \
  --targets "Id=${VM1_INSTANCE_ID},Port=8000"

# Listener HTTP (redireciona para HTTPS se domínio configurado)
aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP --port 80 \
  --default-actions "Type=forward,TargetGroupArn=${TG_ARN}" > /dev/null

echo "[ALB] ✓ ALB criado: http://$ALB_DNS"

# ---------------------------------------------------------------------------
# 2. AWS WAF — Web ACL com Rate Limiting
# ---------------------------------------------------------------------------
echo "[WAF] Criando Web ACL..."
WAF_ACL_ARN=$(aws wafv2 create-web-acl \
  --name "${PROJECT_NAME}-web-acl" \
  --scope REGIONAL \
  --region "$AWS_REGION" \
  --default-action "Allow={}" \
  --visibility-config \
    "SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=${PROJECT_NAME}WebACL" \
  --rules '[
    {
      "Name": "RateLimitRule",
      "Priority": 1,
      "Action": {"Block": {}},
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitRule"
      }
    }
  ]' \
  --query "Summary.ARN" --output text)

# Associar WAF ao ALB
aws wafv2 associate-web-acl \
  --web-acl-arn "$WAF_ACL_ARN" \
  --resource-arn "$ALB_ARN" \
  --region "$AWS_REGION"

echo "[WAF] ✓ WAF associado ao ALB (rate limit: 2000 req/5min por IP)"

# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
ALB_ARN=$ALB_ARN
ALB_DNS=$ALB_DNS
WAF_ACL_ARN=$WAF_ACL_ARN
EOF

echo ""
echo "✅ [07/07] ALB + WAF configurados!"
echo "   Portal (via ALB): http://$ALB_DNS"
echo ""
echo "=============================================="
echo " 🎉 INFRAESTRUTURA AWS COMPLETAMENTE PRONTA!"
echo "=============================================="
echo " Próximos passos:"
echo "   1. Provisione as VMs via SSH (setup.sh de cada VM)"
echo "   2. Faça o build e deploy do frontend (frontend/deploy.sh)"
echo "   3. Configure o Galileo Gen 2 (edge-device/scripts/)"
echo "   4. Teste com: infrastructure/vm3-ctf/scripts/health_check.sh"
