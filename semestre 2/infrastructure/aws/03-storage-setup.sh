#!/usr/bin/env bash
# =============================================================================
# Script 03: S3 (Frontend) + CloudFront
# CTF IIoT Dinâmico — Console-to-Code (AWS CLI)
# =============================================================================
set -euo pipefail

source "$(dirname "$0")/.env"
DEPLOYED="$(dirname "$0")/.deployed-ips"
source "$DEPLOYED"

echo "=============================================="
echo " [03/07] Configurando S3 + CloudFront"
echo "=============================================="

BUCKET_NAME="${PROJECT_NAME}-frontend-$(echo $AWS_ACCOUNT_ID | tail -c 6)"

# ---------------------------------------------------------------------------
# 1. Criar bucket S3 para o frontend React
# ---------------------------------------------------------------------------
echo "[S3] Criando bucket: $BUCKET_NAME..."
if [ "$AWS_REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION"
else
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi

# Bloquear acesso público direto (CloudFront será o único ponto de entrada)
aws s3api put-public-access-block --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

echo "[S3] ✓ Bucket criado: $BUCKET_NAME"

# ---------------------------------------------------------------------------
# 2. Criar Origin Access Control para CloudFront
# ---------------------------------------------------------------------------
echo "[CF] Criando Origin Access Control..."

OAC_ID=$(aws cloudfront create-origin-access-control \
  --origin-access-control-config \
    "Name=${PROJECT_NAME}-oac,Description=OAC para ${PROJECT_NAME},SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" \
  --query "OriginAccessControl.Id" --output text)

echo "[CF] OAC criado: $OAC_ID"

# ---------------------------------------------------------------------------
# 3. Criar distribuição CloudFront
# ---------------------------------------------------------------------------
echo "[CF] Criando distribuição CloudFront..."

CF_CONFIG=$(cat << EOF
{
  "CallerReference": "${PROJECT_NAME}-$(date +%s)",
  "Comment": "CTF IIoT Dinâmico - Portal do Jogador",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${BUCKET_NAME}",
        "DomainName": "${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com",
        "OriginAccessControlId": "${OAC_ID}",
        "S3OriginConfig": { "OriginAccessIdentity": "" }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${BUCKET_NAME}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "AllowedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] },
    "Compress": true
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 0
      }
    ]
  },
  "PriceClass": "PriceClass_100",
  "Enabled": true,
  "HttpVersion": "http2"
}
EOF
)

CF_DIST=$(aws cloudfront create-distribution \
  --distribution-config "$CF_CONFIG" \
  --query "Distribution.{Id:Id,Domain:DomainName}" \
  --output json)

CF_ID=$(echo "$CF_DIST" | jq -r ".Id")
CF_DOMAIN=$(echo "$CF_DIST" | jq -r ".Domain")

echo "[CF] ✓ Distribuição criada: $CF_DOMAIN"

# ---------------------------------------------------------------------------
# 4. Bucket Policy: permitir acesso apenas do CloudFront
# ---------------------------------------------------------------------------
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Sid\": \"AllowCloudFrontOnly\",
    \"Effect\": \"Allow\",
    \"Principal\": {\"Service\": \"cloudfront.amazonaws.com\"},
    \"Action\": \"s3:GetObject\",
    \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}/*\",
    \"Condition\": {
      \"StringEquals\": {
        \"AWS:SourceArn\": \"arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${CF_ID}\"
      }
    }
  }]
}"

# ---------------------------------------------------------------------------
# 5. Salvar
# ---------------------------------------------------------------------------
cat >> "$DEPLOYED" << EOF
S3_BUCKET=$BUCKET_NAME
CF_DISTRIBUTION_ID=$CF_ID
CF_DOMAIN=$CF_DOMAIN
EOF

echo ""
echo "✅ [03/07] S3 + CloudFront configurados!"
echo "   Bucket : $BUCKET_NAME"
echo "   Portal  : https://$CF_DOMAIN"
echo "   (A distribuição CloudFront leva ~15 min para propagar)"
