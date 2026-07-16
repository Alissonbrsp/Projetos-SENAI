#!/usr/bin/env bash
# =============================================================================
# VM3 — User Data Script (executado no primeiro boot pela AWS)
# Instala Docker, copia configs e sobe o ambiente CTF
#
# ⚠️  FLAG 2 está neste script (intencionalmente).
# Credenciais do MQTT admin expostas em texto claro no User Data.
# Acessível via: curl http://169.254.169.254/latest/user-data
# IMDSv1 habilitado intencionalmente para o desafio.
# =============================================================================
set -euo pipefail
exec > /var/log/ctf-userdata.log 2>&1

echo "[$(date)] Iniciando bootstrap VM3 CTF Arena..."

# ---------------------------------------------------------------------------
# Credenciais injetadas via User Data — FLAG 2 está aqui
# Em produção real, use AWS Secrets Manager ou SSM Parameter Store!
# ---------------------------------------------------------------------------
export MQTT_ADMIN_USER="mqtt_admin"
export MQTT_ADMIN_PASS="Br0k3r_4dm1n_P4ss!"
export MQTT_HOST="VM2_BROKER_IP_PLACEHOLDER"  # substituído pelo script 05-compute-setup.sh
export INFLUX_ADMIN_USER="influx_admin"
export INFLUX_ADMIN_PASS="1nflux_S3cur3_P4ss!"
export INFLUX_DB="ctf_sensors"
# FLAG: FLAG{M3t4d4t4_S3rv1c3_3xp0s3s_S3cr3ts}

# ---------------------------------------------------------------------------
# 1. Atualizar sistema e instalar dependências
# ---------------------------------------------------------------------------
apt-get update -y
apt-get install -y curl gnupg2 lsb-release ca-certificates openssh-server \
                   docker.io docker-compose-plugin git

systemctl enable docker
systemctl start docker

# Adicionar usuário padrão ao grupo docker
usermod -aG docker admin 2>/dev/null || true

# ---------------------------------------------------------------------------
# 2. Diretório do CTF
# ---------------------------------------------------------------------------
mkdir -p /opt/ctf/{telegraf,grafana/provisioning/datasources,grafana/provisioning/flag,vulnerable-api}
cd /opt/ctf

# ---------------------------------------------------------------------------
# 3. Flag 4: arquivo dentro do container Grafana
# ---------------------------------------------------------------------------
echo "FLAG{Gr4f4n4_CVE_2021_43798_P4th_Tr4v3rs4l}" > /opt/ctf/grafana/flag4.txt

# ---------------------------------------------------------------------------
# 4. Flag 5: arquivo no filesystem do host (acessível via container escape)
# ---------------------------------------------------------------------------
echo "FLAG{SU1D_D0ck3r_S0ck3t_C0nt41n3r_3sc4p3_GG}" > /root/flag5.txt
chmod 600 /root/flag5.txt

# ---------------------------------------------------------------------------
# 5. Configuração do Telegraf
# ---------------------------------------------------------------------------
cat > /opt/ctf/telegraf/telegraf.conf << TELEGRAF_EOF
[agent]
  interval = "10s"
  flush_interval = "10s"
  hostname = "vm3-ctf"

[[inputs.mqtt_consumer]]
  servers = ["tcp://${MQTT_HOST}:1883"]
  topics = ["fabrica/#"]
  username = "telegraf"
  password = "T3l3gr4f_P4ss!"
  data_format = "json"
  json_string_fields = []

[[outputs.influxdb]]
  urls = ["http://influxdb:8086"]
  database = "${INFLUX_DB}"
  username = "${INFLUX_ADMIN_USER}"
  password = "${INFLUX_ADMIN_PASS}"
TELEGRAF_EOF

# ---------------------------------------------------------------------------
# 6. Datasource do Grafana
# ---------------------------------------------------------------------------
cat > /opt/ctf/grafana/provisioning/datasources/influxdb.yml << DATASOURCE_EOF
apiVersion: 1
datasources:
  - name: InfluxDB
    type: influxdb
    url: http://influxdb:8086
    database: ${INFLUX_DB}
    user: ${INFLUX_ADMIN_USER}
    secureJsonData:
      password: "${INFLUX_ADMIN_PASS}"
    isDefault: true
DATASOURCE_EOF

# ---------------------------------------------------------------------------
# 7. Subir o Docker Compose
# ---------------------------------------------------------------------------
cd /opt/ctf
docker compose up -d

echo "[$(date)] ✅ VM3 CTF Arena pronta!"
docker compose ps
