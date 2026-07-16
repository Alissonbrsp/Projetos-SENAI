# Guia do Administrador — CTF IIoT Dinâmico

## 1. Pré-requisitos

### 1.1 Ferramentas Necessárias

```bash
# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
aws configure  # Configure com suas credenciais de admin

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.10+
sudo apt-get install -y python3.10 python3-pip python3-venv

# jq (para processar JSON dos scripts AWS)
sudo apt-get install -y jq
```

### 1.2 Configuração Inicial

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ctf-iiot-dinamico.git
cd ctf-iiot-dinamico

# Copie e edite o arquivo de variáveis de ambiente
cp infrastructure/aws/.env.example infrastructure/aws/.env
```

Edite `infrastructure/aws/.env` com os valores do seu ambiente:

```bash
# infrastructure/aws/.env
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
PROJECT_NAME=ctf-iiot
ADMIN_IP=200.200.200.200/32    # Seu IP fixo para acesso SSH
KEY_PAIR_NAME=ctf-iiot-key
DOMAIN_NAME=ctf.seudominio.com  # Opcional
```

---

## 2. Deploy Completo (Passo a Passo)

### 2.1 Infraestrutura AWS

Execute os scripts na ordem numerada:

```bash
cd infrastructure/aws

# Torna todos executáveis
chmod +x *.sh

# 1. Criar IAM Roles e Políticas
./01-iam-setup.sh

# 2. Criar VPC, Subnets, Security Groups, Elastic IPs
./02-network-setup.sh

# 3. Criar S3 (frontend) e CloudFront
./03-storage-setup.sh

# 4. Criar RDS PostgreSQL e ElastiCache Redis
./04-database-setup.sh
# ⚠️ Este passo pode levar 10-15 minutos

# 5. Lançar as 3 instâncias EC2
./05-compute-setup.sh
# ⚠️ Anote os Elastic IPs das 3 VMs

# 6. Configurar API Gateway e Lambda
./06-serverless-setup.sh

# 7. Configurar ALB e WAF
./07-waf-setup.sh
```

Após a execução, os IPs estarão em `infrastructure/aws/.deployed-ips`:
```bash
cat infrastructure/aws/.deployed-ips
# VM1_IP=xx.xx.xx.xx
# VM2_IP=xx.xx.xx.xx
# VM3_IP=xx.xx.xx.xx
# RDS_ENDPOINT=xxx.us-east-1.rds.amazonaws.com
# REDIS_ENDPOINT=xxx.cache.amazonaws.com
```

### 2.2 Provisionamento das VMs

```bash
# Carregar IPs automaticamente
source infrastructure/aws/.deployed-ips

# ---- VM1: Management ----
scp -i ~/.ssh/ctf-iiot-key.pem \
    infrastructure/vm1-management/setup.sh \
    ubuntu@$VM1_IP:~/

ssh -i ~/.ssh/ctf-iiot-key.pem ubuntu@$VM1_IP \
    "export RDS_ENDPOINT=$RDS_ENDPOINT; \
     export REDIS_ENDPOINT=$REDIS_ENDPOINT; \
     export VM3_IP=$VM3_IP; \
     bash setup.sh"

# ---- VM2: Broker ----
scp -i ~/.ssh/ctf-iiot-key.pem \
    infrastructure/vm2-broker/setup.sh \
    ubuntu@$VM2_IP:~/

ssh -i ~/.ssh/ctf-iiot-key.pem ubuntu@$VM2_IP "bash setup.sh"

# ---- VM3: CTF Arena ----
# VM3 é provisionada automaticamente via User Data ao criar a EC2.
# Para verificar se está pronto:
ssh -i ~/.ssh/ctf-iiot-key.pem admin@$VM3_IP "docker-compose -f /opt/ctf/docker-compose.yml ps"
```

### 2.3 Build e Deploy do Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Editar variáveis de ambiente do build
cp .env.example .env
nano .env
# REACT_APP_API_URL=https://api.ctf.seudominio.com
# REACT_APP_CLOUDFRONT_URL=https://ctf.seudominio.com

# Build de produção
npm run build

# Deploy para S3 + invalidação do CloudFront
./deploy.sh
```

### 2.4 Configuração do Dispositivo de Borda

Consulte [`edge-device/yocto/README.md`](../edge-device/yocto/README.md) para o build completo do Yocto Linux.

Após flashear o SD card e ligar o Galileo:

```bash
# Descobrir o IP do Galileo via seu roteador ou scanner
nmap -sn 192.168.1.0/24

# Copiar o script do sensor
scp -i ~/.ssh/galileo.pem \
    edge-device/scripts/sensor.py \
    jao@<GALILEO_IP>:~/

# Conectar e configurar
ssh jao@<GALILEO_IP>
pip3 install paho-mqtt smbus2

# Editar o broker IP no script
nano sensor.py  # Ajustar BROKER_HOST = "<VM2_ELASTIC_IP>"

# Testar
python3 sensor.py

# Configurar execução automática no boot
sudo cp sensor.py /opt/sensor.py
sudo systemctl enable ctf-sensor
```

---

## 3. Operação e Manutenção

### 3.1 Reset do Ambiente CTF

**Reset Rápido (~20 segundos)** — Recria apenas os containers:
```bash
source infrastructure/aws/.deployed-ips
ssh -i ~/.ssh/ctf-iiot-key.pem admin@$VM3_IP \
    "cd /opt/ctf && sudo docker-compose down && sudo docker-compose up -d"
```

Ou via endpoint do backend (autenticado como admin):
```bash
curl -X POST "https://api.ctf.seudominio.com/api/admin/reset" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

**Reset Completo (~5 minutos)** — Recria a VM3 a partir da AMI:
```bash
# Usando o script de conveniência
./infrastructure/vm3-ctf/scripts/reset_ctf.sh --full
```

### 3.2 Health Check

```bash
# Verificar todos os serviços
./infrastructure/vm3-ctf/scripts/health_check.sh
```

Saída esperada:
```
[✓] VM1 FastAPI         → HTTP 200 (api.ctf.seudominio.com/health)
[✓] VM2 Mosquitto       → MQTT Connected (broker.ctf.seudominio.com:1883)
[✓] VM3 Grafana         → HTTP 200 (VM3_IP:80)
[✓] VM3 InfluxDB        → HTTP 200 (VM3_IP:8086/ping)
[✓] VM3 Vulnerable API  → HTTP 200 (VM3_IP:5000/health)
[✓] Telegraf → InfluxDB → Data flowing
[✓] Galileo → Mosquitto → Data flowing
```

### 3.3 Monitoramento de Jogadores

```bash
# Ver sessões ativas (Redis)
redis-cli -h $REDIS_ENDPOINT KEYS "session:*"

# Ver logs do backend
ssh ubuntu@$VM1_IP "sudo journalctl -u ctf-backend -f"

# Ver logs do Mosquitto (para ver jogadores se conectando)
ssh ubuntu@$VM2_IP "sudo journalctl -u mosquitto -f"

# Ver logs dos containers na VM3
ssh admin@$VM3_IP "cd /opt/ctf && sudo docker-compose logs -f"
```

### 3.4 Limitar/Gerenciar Jogadores

O sistema aceita no máximo **5 jogadores simultâneos**. Para alterar:

```bash
# No arquivo de configuração do backend (VM1)
sudo nano /opt/ctf-backend/.env
# MAX_CONCURRENT_PLAYERS=5  ← altere este valor
sudo systemctl restart ctf-backend
```

---

## 4. Custos AWS Estimados

| Recurso | Tipo | Custo/mês (estimado) |
|---------|------|---------------------|
| VM1 (EC2 t3.small) | Always-On | ~$15 |
| VM2 (EC2 t3.micro) | Always-On | ~$8 |
| VM3 (EC2 t3.medium) | On-Demand (8h/dia) | ~$10 |
| RDS PostgreSQL (db.t3.micro) | Always-On | ~$15 |
| ElastiCache Redis (cache.t3.micro) | Always-On | ~$12 |
| CloudFront + S3 | Pay-per-use | ~$2 |
| ALB | Always-On | ~$18 |
| AWS WAF | Pay-per-use | ~$5 |
| Elastic IPs (3x) | Always-On | ~$11 |
| **Total estimado** | | **~$96/mês** |

> 💡 **Dica de economia**: Desligue as VMs 1 e 2 quando o CTF não estiver em uso. Com a VM3 sendo On-Demand, o custo pode cair significativamente fora dos períodos de competição.

---

## 5. Criação da AMI Golden Image (VM3)

Após configurar a VM3 completamente:

```bash
# Via AWS CLI
source infrastructure/aws/.deployed-ips
VM3_INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=ip-address,Values=$VM3_IP" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

aws ec2 create-image \
  --instance-id $VM3_INSTANCE_ID \
  --name "ctf-iiot-vm3-golden-$(date +%Y%m%d)" \
  --description "Golden Image VM3 CTF Arena" \
  --no-reboot

echo "AMI em criação. Aguarde ~10 minutos."
```

Atualize o script `06-serverless-setup.sh` com o novo AMI ID para que a Lambda use essa imagem no reset completo.

---

## 6. Troubleshooting

### Galileo não conecta ao broker
```bash
# Testar conectividade MQTT a partir de outra máquina
mosquitto_sub -h <VM2_IP> -p 1883 -u sensor01 -P "S3ns0r01_P4ss!" -t "#" -v

# Verificar logs do Mosquitto
ssh ubuntu@$VM2_IP "sudo journalctl -u mosquitto -n 50"

# Verificar Security Group da VM2 (porta 1883 aberta?)
aws ec2 describe-security-groups --group-names "SG-VM2-Broker"
```

### Grafana não carrega na VM3
```bash
ssh admin@$VM3_IP "cd /opt/ctf && sudo docker-compose ps"
ssh admin@$VM3_IP "cd /opt/ctf && sudo docker-compose logs grafana"
# Reset rápido se necessário:
ssh admin@$VM3_IP "cd /opt/ctf && sudo docker-compose restart grafana"
```

### Sessão máxima atingida (jogadores bloqueados)
```bash
# Verificar e limpar sessões órfãs no Redis
redis-cli -h $REDIS_ENDPOINT GET active_sessions
redis-cli -h $REDIS_ENDPOINT SET active_sessions 0  # Reset forçado
```
