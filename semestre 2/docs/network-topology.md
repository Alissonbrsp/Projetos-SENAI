# Topologia de Rede e Endereçamento

## 1. Visão Geral do Endereçamento

| Recurso | IP / CIDR | Tipo | Observação |
|---------|-----------|------|------------|
| VPC AWS | `10.0.0.0/16` | Privado | Espaço de endereço principal |
| Subnet Pública (AZ-a) | `10.0.1.0/24` | Pública | VM1, VM2, ALB |
| Subnet Pública (AZ-b) | `10.0.2.0/24` | Pública | Redundância ALB |
| Subnet Privada (AZ-a) | `10.0.10.0/24` | Privada | RDS, ElastiCache |
| VM1 (Management) | EIP estático | Público | Nginx + FastAPI |
| VM2 (Broker) | EIP estático | Público | Mosquitto MQTT |
| VM3 (CTF Arena) | EIP estático | Público | Docker CTF |
| RDS PostgreSQL | `10.0.10.x` | Privado | Apenas VM1 acessa |
| ElastiCache Redis | `10.0.10.x` | Privado | Apenas VM1 acessa |

---

## 2. Security Groups

### SG-ALB (Application Load Balancer)
```
Inbound:
  TCP 80  (HTTP)  → 0.0.0.0/0     # Tráfego web
  TCP 443 (HTTPS) → 0.0.0.0/0     # Tráfego web seguro

Outbound:
  TCP 8000 → SG-VM1               # Repassa para o FastAPI
```

### SG-VM1 (Management)
```
Inbound:
  TCP 8000 → SG-ALB               # FastAPI (do ALB)
  TCP 80   → SG-ALB               # Nginx (do ALB)
  TCP 22   → AdminIP/32           # SSH de administração

Outbound:
  TCP 5432 → SG-RDS               # PostgreSQL
  TCP 6379 → SG-ElastiCache       # Redis
  TCP 22   → SG-VM3               # Reset remoto via SSH
  TCP 443  → 0.0.0.0/0            # AWS SDK (boto3), pip
```

### SG-VM2 (Broker)
```
Inbound:
  TCP 1883 → 0.0.0.0/0            # MQTT (Galileo + Telegraf)
  TCP 22   → AdminIP/32           # SSH de administração

Outbound:
  Sem restrições adicionais
```

### SG-VM3 (CTF Arena)
```
Inbound:
  TCP 80   → 0.0.0.0/0            # Grafana (acesso do jogador)
  TCP 5000 → 0.0.0.0/0            # Vulnerable API (acesso do jogador)
  TCP 8086 → SG-VM3               # InfluxDB (apenas containers internos)
  TCP 22   → AdminIP/32, SG-VM1   # SSH: admin + reset da VM1

Outbound:
  TCP 1883 → SG-VM2               # Telegraf → Mosquitto
  TCP 443  → 0.0.0.0/0            # Docker pull, pip
  # BLOQUEADO: TCP any → SG-VM1   # VM3 NÃO pode acessar VM1
  # BLOQUEADO: TCP any → SG-VM2 exceto porta 1883
```

### SG-RDS (Banco de Dados)
```
Inbound:
  TCP 5432 → SG-VM1               # Apenas VM1 acessa o PostgreSQL

Outbound:
  Sem saída necessária
```

### SG-ElastiCache (Redis)
```
Inbound:
  TCP 6379 → SG-VM1               # Apenas VM1 acessa o Redis

Outbound:
  Sem saída necessária
```

---

## 3. Topologia de Rede Detalhada

```
                              INTERNET
                                 │
                    ┌────────────┴────────────┐
                    │        AWS WAF          │
                    │   (Rate Limiting)       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Application Load       │
                    │  Balancer (ALB)         │
                    │  SG-ALB                 │
                    └────────────┬────────────┘
                                 │ :8000
              ┌──────────────────┼──────────────────────┐
              │                  │                       │
    ┌─────────▼──────┐  ┌───────▼──────┐  ┌────────────▼──────┐
    │   VM1          │  │   VM2        │  │   VM3             │
    │   Management   │  │   Broker     │  │   CTF Arena       │
    │   SG-VM1       │  │   SG-VM2     │  │   SG-VM3          │
    │                │  │              │  │                   │
    │ Nginx :80      │  │ Mosquitto    │  │ Grafana :80       │
    │ FastAPI :8000  │  │ MQTT :1883   │  │ Vuln API :5000    │
    │ PostgreSQL     │  │              │  │ InfluxDB :8086    │
    │ Redis          │  │              │  │ Telegraf          │
    └────────┬───────┘  └──────┬───────┘  └────────────────────┘
             │                 │                    │
             │ TCP :5432       │ TCP :1883          │ TCP :1883
             │ TCP :6379       └────────────────────┘
             │                   (Telegraf → Mosquitto)
    ┌────────▼───────────────────────────┐
    │         SUBNET PRIVADA             │
    │  RDS PostgreSQL  :10.0.10.x:5432  │
    │  ElastiCache Redis :10.0.10.x:6379 │
    └────────────────────────────────────┘
```

---

## 4. Portas e Serviços por VM

### VM1 — Management
| Porta | Protocolo | Serviço | Acesso |
|-------|-----------|---------|--------|
| 22 | TCP | SSH (OpenSSH) | Admin IP |
| 80 | TCP | Nginx (HTTP) | ALB → CloudFront |
| 8000 | TCP | Uvicorn/FastAPI | Interno (Nginx → FastAPI) |

### VM2 — Broker
| Porta | Protocolo | Serviço | Acesso |
|-------|-----------|---------|--------|
| 22 | TCP | SSH (OpenSSH) | Admin IP |
| 1883 | TCP | MQTT (Mosquitto) | Galileo + VM3/Telegraf |
| 8883 | TCP | MQTTS (TLS) | Reservado (não ativo no CTF) |

### VM3 — CTF Arena
| Porta | Protocolo | Serviço/Container | Acesso |
|-------|-----------|-------------------|--------|
| 22 | TCP | SSH (OpenSSH) | Admin IP + VM1 |
| 80 | TCP | Grafana (container) | Jogador |
| 5000 | TCP | Vulnerable API (container) | Jogador |
| 8086 | TCP | InfluxDB (container) | Interno (containers) |

---

## 5. Endereçamento do Dispositivo de Borda

| Atributo | Valor |
|----------|-------|
| Dispositivo | Intel Galileo Gen 2 |
| Interface | `eth0` (Ethernet) |
| Configuração IP | DHCP (ou IP fixo configurável em `sensor.py`) |
| Broker MQTT alvo | `<VM2_ELASTIC_IP>:1883` |
| Usuário MQTT | `sensor01` |
| Tópicos publicados | `fabrica/sensor01/temperatura`, `fabrica/sensor01/umidade`, `fabrica/sensor01/luminosidade` |

---

## 6. Configuração DNS (Opcional)

Para produção, configurar no **Route 53**:

| Record | Tipo | Valor |
|--------|------|-------|
| `ctf.seudominio.com` | CNAME | Distribuição CloudFront |
| `api.ctf.seudominio.com` | A | Elastic IP VM1 |
| `broker.ctf.seudominio.com` | A | Elastic IP VM2 |

---

## 7. Regras de Firewall Resumidas (Política Default: DENY ALL)

```
ALLOW: 0.0.0.0/0    → ALB        : 80, 443     # Acesso público ao portal
ALLOW: 0.0.0.0/0    → VM2        : 1883        # MQTT do Galileo
ALLOW: 0.0.0.0/0    → VM3        : 80, 5000    # Acesso ao CTF
ALLOW: AdminIP      → VM1, VM2, VM3 : 22       # SSH de administração
ALLOW: SG-ALB       → SG-VM1     : 8000        # ALB → FastAPI
ALLOW: SG-VM1       → SG-RDS     : 5432        # Backend → PostgreSQL
ALLOW: SG-VM1       → SG-ELC     : 6379        # Backend → Redis
ALLOW: SG-VM1       → SG-VM3     : 22          # Reset remoto
ALLOW: SG-VM3       → SG-VM2     : 1883        # Telegraf → Mosquitto

DENY:  SG-VM3       → SG-VM1     : ALL         # Isolamento da arena
DENY:  SG-VM3       → SG-RDS     : ALL         # Protege o banco
DENY:  *            → *          : ALL         # Default deny
```
