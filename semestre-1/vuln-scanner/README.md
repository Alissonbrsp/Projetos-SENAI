# VulnScanner 🔍
Scanner passivo de vulnerabilidades de rede — Nmap + NVD/CVE + NIST SP 800-53 + CIS Controls v8.

---

## 🔑 Chaves de API necessárias

### NVD API Key — National Vulnerability Database (GRATUITA)
Usada para correlacionar serviços detectados com CVEs reais.

**Como obter:**
1. Acesse: https://nvd.nist.gov/developers/request-an-api-key
2. Preencha seu nome e e-mail
3. Clique em **"Request Key"**
4. Confirme o e-mail recebido
5. Copie a chave gerada

**Onde colocar:**
No arquivo `backend/.env`, na linha:
```
NVD_API_KEY=sua-chave-aqui
```

| Sem chave | Com chave |
|-----------|-----------|
| 5 req / 30s | 50 req / 30s |

> Sem a chave o sistema funciona, porém é mais lento em redes com muitos hosts.

---

## 🖥️ O que instalar

### 1. Nmap
```cmd
winget install Insecure.Nmap
```
Ou baixe em: https://nmap.org/download.html  
⚠️ Marque **"Add to PATH"** durante a instalação.

### 2. Python 3.11+
```cmd
winget install Python.Python.3.11
```
⚠️ Marque **"Add Python to PATH"** durante a instalação.

### 3. Node.js 20+
```cmd
winget install OpenJS.NodeJS.LTS
```

---

## 🚀 Configuração inicial (faça apenas uma vez)

### Backend
```cmd
cd vuln-scanner\backend

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
notepad .env
```

No `.env`, configure obrigatoriamente:
- `SECRET_KEY` — gere com: `python -c "import secrets; print(secrets.token_hex(32))"`
- `NVD_API_KEY` — obtida no passo anterior

### Frontend
```cmd
cd vuln-scanner\frontend
npm install
```

---

## ▶️ Rodar o projeto

Abra **dois terminais CMD**:

**Terminal 1 — Backend:**
```cmd
cd vuln-scanner\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```cmd
cd vuln-scanner\frontend
npm run dev
```

Acesse: **http://localhost:5173**  
Swagger: **http://localhost:8000/docs**

---

## 📁 Estrutura do projeto

```
vuln-scanner/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── config.py            # Configurações (.env)
│   │   ├── database.py          # SQLAlchemy assíncrono
│   │   ├── models/              # ORM: User, Scan, Asset, Port, Vulnerability, Log
│   │   ├── schemas/             # Contratos Pydantic v2
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/register  /auth/login
│   │   │   ├── scanner.py       # /scanner/scan   /scanner/scans
│   │   │   ├── dashboard.py     # /dashboard/stats
│   │   │   ├── logs.py          # /logs/
│   │   │   └── reports.py       # /reports/  /reports/{id}/pdf
│   │   ├── services/
│   │   │   ├── nmap_service.py  # Varredura não-intrusiva
│   │   │   ├── cve_service.py   # Correlação NVD + NIST + CIS
│   │   │   └── report_service.py# Geração de PDF
│   │   └── core/
│   │       ├── security.py      # JWT + bcrypt
│   │       └── dependencies.py  # get_current_user
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   ├── Scanner.jsx      # Varredura + CVEs expansíveis
        │   ├── Dashboard.jsx    # Stats + Recharts
        │   ├── Logs.jsx         # Tabela filtrada
        │   └── Reports.jsx      # Download PDF
        ├── components/
        │   └── Sidebar.jsx
        ├── contexts/
        │   └── AuthContext.jsx  # JWT global
        └── services/
            └── api.js           # Axios + interceptors
```

---

## 🔒 Estratégia de varredura passiva

| Flag nmap | Função |
|-----------|--------|
| `-T3` | Timing moderado (não agressivo) |
| `--max-retries 2` | Limita retransmissões |
| `--open` | Apenas portas abertas |
| `-sV` | Detecção de versão de serviço |
| `--version-intensity 3` | Intensidade baixa (0–9) |
| `-O` | Detecção de SO (requer admin) |

Não são usados: scripts de exploração, brute-force, DoS ou flood.

---

## 🌐 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | /auth/register | Registrar usuário |
| POST | /auth/login | Login → JWT |
| POST | /scanner/scan | Iniciar scan (background) |
| GET | /scanner/scan/{id} | Status e resultados |
| GET | /scanner/scans | Histórico |
| GET | /dashboard/stats | Métricas gerais |
| GET | /logs/ | Logs com filtros |
| GET | /reports/ | Lista de relatórios |
| GET | /reports/{id}/pdf | Download PDF |

---

## 🐛 Solução de problemas

| Erro | Solução |
|------|---------|
| `nmap not found` | Reinstale o Nmap e marque "Add to PATH" |
| `ECONNREFUSED` no frontend | Backend não está rodando — inicie o Terminal 1 |
| `cors_origins` error | Certifique-se de usar vírgula sem espaços no .env |
| Scan muito lento | Adicione a `NVD_API_KEY` no .env |
| Erro de permissão no scan | Abra o CMD como Administrador |
| Banco corrompido | Delete `vuln_scanner.db` e reinicie o backend |
