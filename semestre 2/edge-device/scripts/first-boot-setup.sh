#!/usr/bin/env bash
# first-boot-setup.sh — Configuração inicial do Galileo Gen 2 pós-flash
# Execute como root logo após o primeiro boot via SSH
set -euo pipefail

echo "=== Setup Inicial — Intel Galileo Gen 2 ==="

# Instalar biblioteca MQTT via pip3
pip3 install paho-mqtt smbus2

# Copiar script do sensor (deve ser enviado via scp antes)
mkdir -p /opt/sensor
cp /root/sensor.py /opt/sensor/sensor.py
chmod +x /opt/sensor/sensor.py

# Editar IP do broker antes de criar o serviço
echo ""
echo "⚠️  EDITE o IP do broker em /opt/sensor/sensor.py antes de continuar!"
echo "   Procure por: VM2_IP_PLACEHOLDER"
echo "   Substitua pelo Elastic IP da VM2."
read -p "Pressione ENTER após editar..."

# Criar serviço systemd
cat > /etc/systemd/system/ctf-sensor.service << 'EOF'
[Unit]
Description=CTF IIoT Sensor (DHT22 + LDR → MQTT)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/sensor/sensor.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ctf-sensor

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ctf-sensor
systemctl start ctf-sensor

echo ""
echo "✅ Setup concluído!"
echo "   Status: sudo journalctl -u ctf-sensor -f"
