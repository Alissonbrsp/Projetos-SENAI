#!/usr/bin/env bash
# =============================================================================
# VM2 — Setup: Mosquitto MQTT Broker (nativo, sem Docker)
# =============================================================================
set -euo pipefail

echo "============================================"
echo " VM2 Setup: Mosquitto MQTT Broker"
echo "============================================"

apt-get update -y
apt-get install -y mosquitto mosquitto-clients

# ---------------------------------------------------------------------------
# Copiar configurações
# ---------------------------------------------------------------------------
cp /tmp/mosquitto-configs/mosquitto.conf /etc/mosquitto/mosquitto.conf
cp /tmp/mosquitto-configs/acl.conf       /etc/mosquitto/acl.conf

# ---------------------------------------------------------------------------
# Criar arquivo de senhas (mosquitto_passwd faz o hash automaticamente)
# ---------------------------------------------------------------------------
touch /etc/mosquitto/passwd_file

# Usuário: sensor01 — sensor de campo (Flag 2: credenciais no user-data da VM3)
mosquitto_passwd -b /etc/mosquitto/passwd_file sensor01    "S3ns0r01_P4ss!"

# Usuário: mqtt_admin — administrador do broker (publica tópico de flag)
mosquitto_passwd -b /etc/mosquitto/passwd_file mqtt_admin  "Br0k3r_4dm1n_P4ss!"

# Usuário: telegraf — coleta para a VM3
mosquitto_passwd -b /etc/mosquitto/passwd_file telegraf    "T3l3gr4f_P4ss!"

chmod 640 /etc/mosquitto/passwd_file
chown mosquitto:mosquitto /etc/mosquitto/passwd_file /etc/mosquitto/acl.conf

# ---------------------------------------------------------------------------
# Script de publicação da flag MQTT (Flag 3 — roda via cron)
# ---------------------------------------------------------------------------
mkdir -p /opt/ctf
cat > /opt/ctf/publish_flag.sh << 'FLAGSCRIPT'
#!/bin/bash
# Publica a flag no tópico de gerenciamento a cada minuto (retained message)
mosquitto_pub -h localhost -u mqtt_admin -P "Br0k3r_4dm1n_P4ss!" \
  -t "fabrica/sistema/flag" \
  -m "FLAG{ACL_W1ldC4rd_1_C4n_H34r_3v3ryth1ng}" \
  -r -q 1
FLAGSCRIPT
chmod +x /opt/ctf/publish_flag.sh

# Cron: publica a cada minuto
echo "* * * * * root /opt/ctf/publish_flag.sh >> /var/log/ctf-flag3.log 2>&1" \
  > /etc/cron.d/ctf-flag3
chmod 644 /etc/cron.d/ctf-flag3

# ---------------------------------------------------------------------------
# Ativar e iniciar serviços
# ---------------------------------------------------------------------------
systemctl enable mosquitto
systemctl restart mosquitto
systemctl enable cron

echo ""
echo "✅ VM2 configurada!"
echo "   Mosquitto MQTT → porta 1883"
echo "   Usuários: sensor01, mqtt_admin, telegraf"
mosquitto_sub -h localhost -u mqtt_admin -P "Br0k3r_4dm1n_P4ss!" \
  -t "\$SYS/broker/version" -C 1 --quiet && echo "   Broker: OK"
