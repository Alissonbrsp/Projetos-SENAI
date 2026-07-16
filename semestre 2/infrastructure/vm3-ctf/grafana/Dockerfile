FROM grafana/grafana:8.3.0
# Grafana 8.3.0 — versão com CVE-2021-43798 (Path Traversal) para o desafio Flag 4
# Executa como root via docker-compose (user: "0") — Flag 5

USER root

# Criar diretório e flag4
RUN mkdir -p /var/lib/grafana
COPY flag4.txt /var/lib/grafana/flag4.txt

# Garantir permissões corretas no diretório de dados
RUN chown -R root:root /var/lib/grafana && chmod 755 /var/lib/grafana

USER grafana
