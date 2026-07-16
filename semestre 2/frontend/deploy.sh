#!/usr/bin/env bash
# deploy.sh — Build do React e deploy para S3 + invalidação CloudFront
set -euo pipefail

source "../infrastructure/aws/.env"
source "../infrastructure/aws/.deployed-ips"

echo "=== Build do Frontend ==="
npm run build

echo "=== Upload para S3 ==="
aws s3 sync build/ "s3://${S3_BUCKET}/" \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --exclude "index.html"

# index.html sem cache (sempre atualizado)
aws s3 cp build/index.html "s3://${S3_BUCKET}/index.html" \
  --cache-control "no-cache,no-store,must-revalidate" \
  --content-type "text/html"

echo "=== Invalidando cache CloudFront ==="
aws cloudfront create-invalidation \
  --distribution-id "${CF_DISTRIBUTION_ID}" \
  --paths "/*"

echo "✅ Deploy concluído!"
echo "   Portal: https://${CF_DOMAIN}"
