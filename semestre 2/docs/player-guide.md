# Guia do Jogador — CTF IIoT Dinâmico

> **Documento público** — Este é o guia oficial para participantes do CTF.

---

## 🏭 A História

Bem-vindo à **Fábrica Conectada SA** — uma empresa de manufatura que modernizou sua linha de produção com sensores inteligentes conectados à nuvem. Você foi contratado como **Pentester Júnior** para realizar um teste de invasão (pentest) autorizado em toda a infraestrutura.

A missão: percorrer a cadeia de ataque desde o portal web público até o servidor de dados interno, documentando cada falha encontrada ao longo do caminho.

Cada vulnerabilidade que você explorar com sucesso revela uma **flag** no formato `FLAG{...}`. Colete todas as 5 flags para completar o desafio.

---

## 📋 Regras

1. ✅ **Você PODE**: Escanear portas, explorar as vulnerabilidades dos serviços indicados, interagir com qualquer serviço da VM3.
2. ❌ **Você NÃO PODE**: Atacar outros jogadores, destruir dados propositalmente, tentar comprometer a infraestrutura de gerenciamento (VM1 e VM2) — elas estão fora do escopo.
3. ⏱️ Máximo de **5 jogadores simultâneos**. Se o ambiente estiver lotado, você verá uma mensagem de espera no portal.
4. O ambiente pode ser **resetado pelo admin** a qualquer momento se houver corrupção de dados.

---

## 🚀 Como Começar

### 1. Acesse o Portal
Vá para: `https://ctf.seudominio.com`

Registre-se com um e-mail e senha. Faça login.

### 2. Inicie o Ambiente
Clique em **"Iniciar CTF"** no painel. Aguarde 2-3 minutos enquanto o ambiente é preparado na nuvem.

Quando o status mudar para **"Online"**, você verá o **IP do servidor de desafios**.

### 3. Siga a Trilha

As flags são encadeadas — a informação encontrada em uma flag frequentemente é usada para resolver a próxima. Comece sempre pela **Flag 1**.

---

## 🗺️ Mapa dos Desafios

```
[Portal Web] ──► Flag 1 ──► Flag 2 ──► Flag 3 ──► Flag 4 ──► Flag 5
                (1/10)      (3/10)      (6/10)      (7/10)     (9.5/10)
```

### Flag 1 — Fácil (1/10)
**Dica**: Todo desenvolvedor já esqueceu de limpar o código antes de publicar. O que acontece quando alguém "inspeciona" uma página web?

Ferramentas sugeridas: Apenas um navegador web.

---

### Flag 2 — Fácil-Médio (3/10)
**Dica**: Ambientes de nuvem têm um serviço especial que fornece informações sobre a própria máquina. Um endereço IP muito específico — `169.254.169.254` — é famoso por isso. O que você encontra lá dentro da VM do CTF?

Ferramentas sugeridas: `curl`, acesso SSH (credenciais encontradas na Flag 1).

---

### Flag 3 — Médio (6/10)
**Dica**: Sensores industriais "falam" por um protocolo chamado MQTT. Imagine que você tem credenciais de um desses sensores... será que ele consegue "ouvir" mais do que deveria? Experimente se inscrever em um tópico mais amplo do que o esperado.

Ferramentas sugeridas: `mosquitto_sub`, IP do broker obtido na VM (porta 1883).

---

### Flag 4 — Difícil (7/10)
**Dica**: O dashboard de visualização está rodando uma versão um pouco "madura" do software. CVEs não perdoam quem não atualiza. Identifique a versão, pesquise, e veja quais arquivos você consegue acessar sem autenticação.

Ferramentas sugeridas: `curl`, [NVD](https://nvd.nist.gov), navegador.

---

### Flag 5 — Expert (9.5/10)
**Dica**: Você está dentro de um container, mas containers bem configurados são isolados. Este não é bem configurado. Quais permissões especiais este container tem? Existe alguma forma de interagir com o sistema operacional subjacente sem sair pelo caminho convencional?

Ferramentas sugeridas: `find`, `curl`, conhecimento de APIs Unix Sockets, Linux privilege escalation.

---

## 📬 Submetendo Flags

Todas as flags têm o formato: `FLAG{...}`

No painel do CTF, cole a flag no campo **"Submeter Flag"** e clique em **"Verificar"**. O sistema confirmará se a flag está correta e desbloqueará a dica para o próximo desafio.

---

## 🛠️ Ferramentas Recomendadas

```bash
# Para instalar as ferramentas essenciais (Ubuntu/Debian)
sudo apt-get install -y mosquitto-clients curl nmap netcat-openbsd

# Para interagir com MQTT
mosquitto_sub -h <IP_BROKER> -p 1883 -u <usuario> -P <senha> -t "#" -v

# Para testar Path Traversal
curl --path-as-is "http://<IP>:<PORTA>/caminho/../../../arquivo"
```

---

## ❓ FAQ

**P: Posso usar ferramentas automatizadas (Burp Suite, Metasploit, etc.)?**
R: Sim, desde que você não faça DoS no ambiente ou ataque outros jogadores.

**P: O ambiente ficou instável. O que faço?**
R: Aguarde 5 minutos. Se persistir, contate o admin pelo Discord do evento para solicitar um reset.

**P: Perdi o acesso SSH durante o desafio. E agora?**
R: As credenciais SSH foram obtidas na Flag 1. Revise seus anotações. Se necessário, peça um reset.

**P: Posso trabalhar em equipe?**
R: Sim! Apenas certifique-se de que todos os membros da equipe estão usando a mesma conta no portal.

---

## 🏆 Ranking

O ranking é calculado por:
1. Número de flags encontradas
2. Tempo até cada flag (menor tempo = melhor posição)

Boa sorte e **hack ethically!** 🛡️
