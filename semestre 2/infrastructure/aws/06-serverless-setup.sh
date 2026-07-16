#!/usr/bin/env bash
# =============================================================================
# Script 06: API Gateway + Lambda (lifecycle da VM3)
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"
source "$DEPLOYED"

echo "======================================="
echo " [06/07] API Gateway + Lambda"
echo "======================================="

# ---------------------------------------------------------------------------
# 1. Empacotar e fazer upload da Lambda
# ---------------------------------------------------------------------------
echo "[Lambda] Empacotando código..."
cd "$(dirname "$0")/lambda"
zip -q function.zip ec2_lifecycle_manager.py
cd -

LAMBDA_ARN=$(aws lambda create-function \
  --function-name "${PROJECT_NAME}-ec2-lifecycle" \
  --runtime python3.11 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler ec2_lifecycle_manager.lambda_handler \
  --zip-file fileb://$(dirname "$0")/lambda/function.zip \
  --timeout 30 \
  --environment "Variables={VM3_INSTANCE_ID=${VM3_INSTANCE_ID},FRONTEND_URL=${FRONTEND_URL:-*}}" \
  --tags "Project=${PROJECT_NAME}" \
  --query "FunctionArn" --output text)

echo "[Lambda] ✓ Função criada: $LAMBDA_ARN"

# ---------------------------------------------------------------------------
# 2. API Gateway HTTP (v2)
# ---------------------------------------------------------------------------
echo "[APIGW] Criando API Gateway..."
API_ID=$(aws apigatewayv2 create-api \
  --name "${PROJECT_NAME}-session-api" \
  --protocol-type HTTP \
  --cors-configuration \
    "AllowOrigins=[${FRONTEND_URL:-'*'}],AllowMethods=[GET,POST,OPTIONS],AllowHeaders=[Content-Type,Authorization]" \
  --query "ApiId" --output text)

# Integração com a Lambda
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "$LAMBDA_ARN" \
  --payload-format-version "2.0" \
  --query "IntegrationId" --output text)

# Rotas
for METHOD_PATH in "GET /session/status" "POST /session/start" "POST /session/stop"; do
  METHOD=$(echo $METHOD_PATH | cut -d' ' -f1)
  PATH_=$( echo $METHOD_PATH | cut -d' ' -f2)
  aws apigatewayv2 create-route \
    --api-id "$API_ID" \
    --route-key "$METHOD $PATH_" \
    --target "integrations/$INTEGRATION_ID" > /dev/null
done

# Deploy do stage
aws apigatewayv2 create-stage \
  --api-id "$API_ID" \
  --stage-name "prod" \
  --auto-deploy > /dev/null

APIGW_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod"

# Permissão para o API Gateway invocar a Lambda
aws lambda add-permission \
  --function-name "${PROJECT_NAME}-ec2-lifecycle" \
  --statement-id "apigw-invoke" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*" > /dev/null

echo "[APIGW] ✓ API disponível: $APIGW_URL"

# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
LAMBDA_ARN=$LAMBDA_ARN
LAMBDA_API_URL=$APIGW_URL
API_GATEWAY_ID=$API_ID
EOF

echo ""
echo "✅ [06/07] Lambda + API Gateway configurados!"
echo "   Endpoint: $APIGW_URL"
