#!/usr/bin/env bash
# health_check.sh — Verifica saúde de todos os serviços da VM3
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
check() { local name="$1" url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then echo -e "${GREEN}[✓]${NC} $name"
  else echo -e "${RED}[✗]${NC} $name"; fi
}
echo "=== Health Check VM3 CTF Arena ==="
check "InfluxDB    :8086" "http://localhost:8086/ping"
check "Grafana     :80  " "http://localhost:80/api/health"
check "Vuln API    :5000" "http://localhost:5000/health"
echo ""
echo "Docker Compose status:"
docker compose -f /opt/ctf/docker-compose.yml ps
