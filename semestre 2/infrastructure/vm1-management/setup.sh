#!/usr/bin/env bash
# =============================================================================
# VM1 — Setup completo: Nginx + FastAPI + PostgreSQL + Redis
# Execute como root ou com sudo após o SSH na VM1
# =============================================================================
set -euo pipefail

: "${RDS_ENDPOINT:?Variável RDS_ENDPOINT não definida}"
: "${REDIS_ENDPOINT:?Variável REDIS_ENDPOINT não definida}"
: "${VM3_IP:?Variável VM3_IP não definida}"

echo "============================================"
echo " VM1 Setup: Management Portal"
echo "============================================"

# ---------------------------------------------------------------------------
# 1. Dependências do sistema
# ---------------------------------------------------------------------------
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3-pip nginx \
                   postgresql-client certbot python3-certbot-nginx \
                   openssh-client jq curl

# ---------------------------------------------------------------------------
# 2. Usuário e diretório da aplicação
# ---------------------------------------------------------------------------
useradd -r -s /bin/false ctf-backend 2>/dev/null || true
mkdir -p /opt/ctf-backend/{keys,logs}
chown -R ctf-backend:ctf-backend /opt/ctf-backend

# ---------------------------------------------------------------------------
# 3. Clonar o projeto e instalar dependências Python
# ---------------------------------------------------------------------------
cp -r /tmp/ctf-backend-src/* /opt/ctf-backend/  # copiado via scp antes deste script
cd /opt/ctf-backend

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------------------------------------------------------------------------
# 4. Variáveis de ambiente (.env)
# ---------------------------------------------------------------------------
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
ADMIN_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

cat > /opt/ctf-backend/.env << EOF
DATABASE_URL=postgresql://ctf_admin:${DB_PASSWORD:-ChangeMe!}@${RDS_ENDPOINT}:5432/ctf_db
REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
JWT_SECRET_KEY=${JWT_SECRET}
ADMIN_SECRET_TOKEN=${ADMIN_TOKEN}
LAMBDA_API_URL=${LAMBDA_API_URL:-http://localhost}
LAMBDA_API_KEY=${LAMBDA_API_KEY:-}
FRONTEND_URL=${FRONTEND_URL:-*}
MAX_CONCURRENT_PLAYERS=5
TOKEN_EXPIRE_MINUTES=120
VM3_IP=${VM3_IP}
VM3_SSH_KEY_PATH=/opt/ctf-backend/keys/vm3.pem
EOF

chmod 600 /opt/ctf-backend/.env
chown ctf-backend:ctf-backend /opt/ctf-backend/.env

echo "Admin token salvo em /opt/ctf-backend/ADMIN_TOKEN.txt"
echo "$ADMIN_TOKEN" > /opt/ctf-backend/ADMIN_TOKEN.txt
chmod 600 /opt/ctf-backend/ADMIN_TOKEN.txt

# ---------------------------------------------------------------------------
# 5. Inicializar schema do banco (via psql client → RDS)
# ---------------------------------------------------------------------------
PGPASSWORD="${DB_PASSWORD:-ChangeMe!}" psql \
  -h "$RDS_ENDPOINT" -U ctf_admin -d ctf_db \
  -f /opt/ctf-backend/database/schema.sql

# ---------------------------------------------------------------------------
# 6. Systemd service
# ---------------------------------------------------------------------------
cp /opt/ctf-backend/systemd/ctf-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ctf-backend
systemctl start ctf-backend
sleep 2
systemctl status ctf-backend --no-pager

# ---------------------------------------------------------------------------
# 7. Nginx
# ---------------------------------------------------------------------------
cp /opt/ctf-backend/nginx/ctf-portal.conf /etc/nginx/sites-available/ctf
ln -sf /etc/nginx/sites-available/ctf /etc/nginx/sites-enabled/ctf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "✅ VM1 configurada com sucesso!"
echo "   FastAPI  → http://localhost:8000"
echo "   Nginx    → http://$(hostname -I | awk '{print $1}'):80"
echo ""
echo "⚠️  Lembre-se de copiar a chave SSH da VM3 para: /opt/ctf-backend/keys/vm3.pem"
