#!/usr/bin/env bash
# reset_ctf.sh — Recria todos os containers do CTF
set -euo pipefail
cd /opt/ctf
echo "[$(date)] Iniciando reset do ambiente CTF..."
docker compose down --remove-orphans
docker compose up -d
echo "[$(date)] Reset concluído. Containers:"
docker compose ps
