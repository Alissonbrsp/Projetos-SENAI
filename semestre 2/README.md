# 🏭 CTF IIoT Dinâmico

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: AWS](https://img.shields.io/badge/Platform-AWS-orange.svg)](https://aws.amazon.com)
[![IoT: IIoT](https://img.shields.io/badge/Domain-IIoT-blue.svg)]()
[![CTF: 5 Flags](https://img.shields.io/badge/CTF-5%20Flags-red.svg)]()

> Plataforma de treinamento em **Cibersegurança Industrial (IIoT)** no formato Capture The Flag, com infraestrutura híbrida real: dispositivo físico de borda (Intel Galileo Gen 2) + nuvem AWS. Desenvolvida para estudantes e profissionais de segurança ofensiva em ambientes industriais.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Flags e Vulnerabilidades](#flags-e-vulnerabilidades)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Início Rápido](#início-rápido)
- [Documentação](#documentação)
- [Aviso Legal](#aviso-legal)

---

## 🎯 Visão Geral

O **CTF IIoT Dinâmico** simula uma infraestrutura industrial híbrida real, composta por:

- **Dispositivo de Borda Físico**: Intel Galileo Gen 2 rodando Linux embarcado (Yocto), com sensores DHT22 (temperatura/umidade) e LDR (luminosidade), publicando dados via MQTT.
- **Infraestrutura de Nuvem (AWS)**: Três máquinas virtuais com funções especializadas, orquestradas via Docker e serviços gerenciados AWS.
- **Portal do Jogador**: Frontend React com autenticação, painel de status e submissão de flags.
- **5 Vulnerabilidades Progressivas**: Do básico (inspecionar código-fonte) ao avançado (Container Escape).

### Por que IIoT?

Sistemas industriais (SCADA, ICS, IIoT) são alvos crescentes de ataques. Diferente de CTFs convencionais, este projeto expõe falhas realistas de ambientes de manufatura: protocolos legados (MQTT sem autenticação adequada), containers desatualizados em produção, credenciais em pipelines CI/CD e má configuração de permissões em nuvem.

---

## 🏗️ Arquitetura

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        ATORES EXTERNOS                              │
 │  🎮 Jogador/CTF Player          🔌 Intel Galileo Gen 2 (Sensor)    │
 └───────────────┬─────────────────────────────┬───────────────────────┘
                 │ HTTPS                        │ MQTT :1883
                 ▼                              ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │                            AWS CLOUD                              │
 │                                                                   │
 │  ┌──────────────────────────────────────────────────────────┐    │
 │  │         ECOSSISTEMA DE GERENCIAMENTO (ALWAYS-ON)          │    │
 │  │                                                           │    │
 │  │  CloudFront ──► S3 (React)    API Gateway ──► Lambda     │    │
 │  │                               (VM Lifecycle Management)   │    │
 │  │                                                           │    │
 │  │  VM1 – Management (Nginx + FastAPI + PostgreSQL + Redis)  │    │
 │  └──────────────────────────────────────────────────────────┘    │
 │                                                                   │
 │  ┌──────────────────────────────────────────────────────────┐    │
 │  │         VM2 – BROKER DEDICADO (ALWAYS-ON)                │    │
 │  │         Mosquitto MQTT (Nativo, sem Docker)               │    │
 │  └──────────────────────────────────────────────────────────┘    │
 │                                                                   │
 │  ┌──────────────────────────────────────────────────────────┐    │
 │  │         VM3 – ARENA DO CTF (ON-DEMAND / Docker)          │    │
 │  │                                                           │    │
 │  │  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │    │
 │  │  │ InfluxDB │  │ Telegraf │  │  Grafana (vulnerável)  │  │    │
 │  │  └──────────┘  └──────────┘  └───────────────────────┘  │    │
 │  │  ┌──────────────────────────┐                            │    │
 │  │  │  Vulnerable API (isca)   │                            │    │
 │  │  └──────────────────────────┘                            │    │
 │  └──────────────────────────────────────────────────────────┘    │
 └───────────────────────────────────────────────────────────────────┘
```

Para diagrama completo e detalhes de rede, veja [`docs/architecture.md`](docs/architecture.md).

---

## 🚩 Flags e Vulnerabilidades

| # | Vulnerabilidade | Dificuldade | Camada |
|---|----------------|-------------|--------|
| 1 | Credenciais no Código-Fonte do Frontend | ⭐ `1/10` | Frontend |
| 2 | Credenciais no User Data da EC2 (Metadados AWS) | ⭐⭐⭐ `3/10` | Cloud/AWS |
| 3 | ACL Permissiva no Broker MQTT | ⭐⭐⭐⭐⭐⭐ `6/10` | IIoT/Protocolo |
| 4 | Path Traversal em Container Grafana Desatualizado | ⭐⭐⭐⭐⭐⭐⭐ `7/10` | Container/CVE |
| 5 | Privilege Escalation + Container Escape via SUID | ⭐⭐⭐⭐⭐⭐⭐⭐⭐ `9.5/10` | Linux/Container |

Documentação completa em [`docs/vulnerabilities.md`](docs/vulnerabilities.md).

---

## 📁 Estrutura do Repositório

```
ctf-iiot-dinamico/
├── docs/                          # Documentação completa do projeto
│   ├── architecture.md            # Arquitetura detalhada e diagramas
│   ├── vulnerabilities.md         # Guia das 5 vulnerabilidades (admin)
│   ├── admin-guide.md             # Manual de deploy e operação
│   ├── player-guide.md            # Guia e história para o jogador
│   └── network-topology.md        # Endereçamento IP, Security Groups
│
├── infrastructure/
│   ├── aws/                       # Scripts AWS CLI (console-to-code)
│   │   ├── 01-iam-setup.sh        # IAM Roles e Políticas
│   │   ├── 02-network-setup.sh    # VPC, Security Groups, Elastic IP
│   │   ├── 03-storage-setup.sh    # S3, CloudFront
│   │   ├── 04-database-setup.sh   # RDS PostgreSQL, ElastiCache Redis
│   │   ├── 05-compute-setup.sh    # EC2 instances (VM1, VM2, VM3)
│   │   ├── 06-serverless-setup.sh # API Gateway + Lambda
│   │   ├── 07-waf-setup.sh        # AWS WAF + ALB (proteção DDoS)
│   │   ├── iam/                   # Políticas IAM em JSON
│   │   └── lambda/                # Código da Lambda (lifecycle manager)
│   │
│   ├── vm1-management/            # VM1: Portal de Gerenciamento
│   │   ├── setup.sh               # Script de provisionamento completo
│   │   ├── nginx/                 # Configuração do Nginx
│   │   ├── backend/               # Aplicação FastAPI
│   │   └── database/              # Schema do PostgreSQL
│   │
│   ├── vm2-broker/                # VM2: Broker MQTT Dedicado
│   │   ├── setup.sh               # Script de provisionamento
│   │   └── mosquitto/             # Configs do Mosquitto (ACL vulnerável)
│   │
│   └── vm3-ctf/                   # VM3: Arena do CTF (Docker)
│       ├── docker-compose.yml     # Orquestração dos containers
│       ├── user-data.sh           # Bootstrap script (Flag 2 está aqui)
│       ├── telegraf/              # Config do Telegraf
│       ├── grafana/               # Grafana vulnerável (Flag 4 e 5)
│       ├── vulnerable-api/        # API de isca (FastAPI)
│       └── scripts/               # Scripts de reset e health check
│
├── frontend/                      # Portal do Jogador (React)
│   ├── src/
│   │   ├── config.js              # ⚠️  FLAG 1 está aqui (propositalmente)
│   │   ├── pages/                 # Login e Dashboard
│   │   ├── components/            # Componentes reutilizáveis
│   │   └── services/              # Chamadas de API
│   └── deploy.sh                  # Deploy para S3 + invalidação CloudFront
│
└── edge-device/                   # Dispositivo de Borda (Intel Galileo Gen 2)
    ├── yocto/                     # Configurações do build Yocto Linux
    │   ├── local.conf             # Configuração principal do Yocto
    │   └── bblayers.conf          # Camadas do Yocto
    └── scripts/
        ├── sensor.py              # Script principal do sensor MQTT
        └── first-boot-setup.sh    # Setup inicial pós-flash
```

---

## 🚀 Início Rápido

### Pré-requisitos

- **AWS CLI** configurado com credenciais de administrador
- **Node.js 18+** e **npm** (para o frontend)
- **Python 3.10+** (para scripts de setup)
- **Docker** e **Docker Compose** (instalados automaticamente na VM3)
- Um cartão **microSD 8GB+** e um **Intel Galileo Gen 2** (para o edge device)

### Deploy Completo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/ctf-iiot-dinamico.git
cd ctf-iiot-dinamico

# 2. Configure as variáveis de ambiente
cp infrastructure/aws/.env.example infrastructure/aws/.env
nano infrastructure/aws/.env   # Edite com seus valores

# 3. Execute os scripts AWS em ordem
cd infrastructure/aws
chmod +x *.sh
./01-iam-setup.sh
./02-network-setup.sh
./03-storage-setup.sh
./04-database-setup.sh
./05-compute-setup.sh
./06-serverless-setup.sh
./07-waf-setup.sh

# 4. Provisione as VMs (via SSH após as EC2 estarem running)
# VM1
ssh -i sua-chave.pem ubuntu@<VM1_IP> 'bash -s' < infrastructure/vm1-management/setup.sh

# VM2
ssh -i sua-chave.pem ubuntu@<VM2_IP> 'bash -s' < infrastructure/vm2-broker/setup.sh

# VM3 (apenas o setup base; Docker Compose é iniciado via Lambda)
ssh -i sua-chave.pem ubuntu@<VM3_IP> 'bash -s' < infrastructure/vm3-ctf/user-data.sh

# 5. Build e deploy do frontend
cd frontend
npm install
npm run build
./deploy.sh
```

Para guia detalhado, veja [`docs/admin-guide.md`](docs/admin-guide.md).

---

## 📚 Documentação

| Documento | Público | Descrição |
|-----------|---------|-----------|
| [`docs/architecture.md`](docs/architecture.md) | Admin | Arquitetura completa, diagramas, fluxos |
| [`docs/vulnerabilities.md`](docs/vulnerabilities.md) | Admin | Descrição técnica das 5 flags |
| [`docs/admin-guide.md`](docs/admin-guide.md) | Admin | Deploy, manutenção, reset de ambiente |
| [`docs/player-guide.md`](docs/player-guide.md) | Jogador | História, regras e dicas iniciais |
| [`docs/network-topology.md`](docs/network-topology.md) | Admin | IPs, VLANs, Security Groups, regras de firewall |
| [`edge-device/yocto/README.md`](edge-device/yocto/README.md) | Admin | Build do Yocto Linux para o Galileo |

---

## ⚖️ Aviso Legal

> **Este projeto é desenvolvido exclusivamente para fins educacionais em Cibersegurança.**
>
> As vulnerabilidades implementadas são **intencionais** e existem para criar um ambiente de aprendizado controlado. O uso deste projeto em sistemas reais de terceiros sem autorização expressa é ilegal e antiético.
>
> Ao utilizar este projeto, você confirma que o fará apenas em ambientes próprios, com autorização explícita dos responsáveis pela infraestrutura.

---

## 📄 Licença

MIT License — veja o arquivo [LICENSE](LICENSE) para detalhes.
