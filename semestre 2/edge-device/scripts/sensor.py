#!/usr/bin/env python3
"""
CTF IIoT Dinâmico — Script de Sensor do Dispositivo de Borda
Hardware: Intel Galileo Gen 2 | Sensores: DHT22 (temp/umidade) + LDR (luminosidade)
Protocolo: MQTT (paho-mqtt) → VM2 Broker Mosquitto

Uso:
  python3 sensor.py                     # modo hardware (Galileo)
  python3 sensor.py --simulate          # modo simulação (desenvolvimento)
  python3 sensor.py --simulate --debug  # com log verbose
"""

import argparse
import json
import logging
import math
import random
import sys
import time
from datetime import datetime, timezone

# ─── Configuração via argumentos ou variáveis de ambiente ───────────────────
parser = argparse.ArgumentParser(description="Sensor IIoT para Intel Galileo Gen 2")
parser.add_argument("--broker",   default="VM2_IP_PLACEHOLDER", help="IP do broker MQTT (VM2)")
parser.add_argument("--port",     type=int, default=1883, help="Porta MQTT")
parser.add_argument("--user",     default="sensor01", help="Usuário MQTT")
parser.add_argument("--password", default="S3ns0r01_P4ss!", help="Senha MQTT")
parser.add_argument("--client-id",default="galileo-sensor01", help="Client ID MQTT")
parser.add_argument("--interval", type=float, default=5.0, help="Intervalo de leitura (s)")
parser.add_argument("--simulate", action="store_true", help="Usar dados simulados (sem hardware)")
parser.add_argument("--debug",    action="store_true", help="Log detalhado")
args = parser.parse_args()

logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("sensor")

# ─── Importar paho-mqtt ──────────────────────────────────────────────────────
try:
    import paho.mqtt.client as mqtt
except ImportError:
    log.error("paho-mqtt não instalado. Execute: pip3 install paho-mqtt")
    sys.exit(1)

# ─── Importar bibliotecas de sensor (apenas em modo hardware) ───────────────
if not args.simulate:
    try:
        import smbus2
        log.info("smbus2 carregado (modo hardware I2C)")
    except ImportError:
        log.warning("smbus2 não disponível. Alternando para modo simulação.")
        args.simulate = True

# ─── Leitura do DHT22 (temperatura e umidade) ───────────────────────────────
# O DHT22 no Galileo Gen 2 é lido via interface GPIO/I2C
# Em ambientes sem hardware físico, usamos o modo simulado

def ler_dht22_hardware():
    """Lê temperatura e umidade do sensor DHT22 via I2C (Galileo Gen 2)."""
    try:
        bus = smbus2.SMBus(0)  # I2C bus 0 no Galileo Gen 2
        # Endereço I2C do módulo DHT22 com interface I2C (ex: Si7021 compatível)
        dados = bus.read_i2c_block_data(0x40, 0xF5, 6)  # addr=0x40, cmd medição
        time.sleep(0.02)
        dados = bus.read_i2c_block_data(0x40, 0x00, 6)
        umidade_raw    = (dados[0] << 8) | dados[1]
        temperatura_raw = (dados[3] << 8) | dados[4]
        umidade    = round(((umidade_raw    / 65536.0) * 125.0) - 6.0, 1)
        temperatura = round(((temperatura_raw / 65536.0) * 175.72) - 46.85, 1)
        bus.close()
        return temperatura, umidade
    except Exception as e:
        log.warning(f"Erro ao ler DHT22: {e} — usando fallback simulado")
        return simular_temperatura(), simular_umidade()


def ler_ldr_hardware():
    """Lê luminosidade do sensor LDR via ADC do Galileo."""
    try:
        # Galileo Gen 2: pinos analógicos mapeados via sysfs
        with open("/sys/bus/iio/devices/iio:device0/in_voltage0_raw") as f:
            raw = int(f.read().strip())
        # ADC 12-bit, referência 5V → converte para lux (aproximado)
        lux = round((raw / 4095.0) * 1000.0, 1)
        return lux
    except Exception as e:
        log.warning(f"Erro ao ler LDR: {e} — usando fallback simulado")
        return simular_luminosidade()


# ─── Funções de simulação (modo desenvolvimento) ────────────────────────────
_sim_t_base = 22.5
_sim_tick   = 0

def simular_temperatura():
    global _sim_tick
    _sim_tick += 1
    return round(_sim_t_base + math.sin(_sim_tick * 0.1) * 3 + random.uniform(-0.3, 0.3), 1)

def simular_umidade():
    return round(55.0 + random.uniform(-8, 8), 1)

def simular_luminosidade():
    hora = datetime.now().hour
    if 6 <= hora <= 18:
        return round(600 + random.uniform(-100, 200), 1)
    return round(30 + random.uniform(-10, 20), 1)


# ─── Leitura unificada ───────────────────────────────────────────────────────
def ler_sensores():
    if args.simulate:
        temperatura = simular_temperatura()
        umidade     = simular_umidade()
        luminosidade = simular_luminosidade()
    else:
        temperatura, umidade = ler_dht22_hardware()
        luminosidade = ler_ldr_hardware()

    return {
        "sensor_id":     "sensor01",
        "location":      "linha-a",
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "temperatura":   temperatura,
        "umidade":       umidade,
        "luminosidade":  luminosidade,
        "mode":          "simulate" if args.simulate else "hardware",
    }


# ─── MQTT ────────────────────────────────────────────────────────────────────
TOPIC_BASE = "fabrica/sensor01"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info(f"✅ Conectado ao broker MQTT {args.broker}:{args.port}")
    else:
        log.error(f"❌ Falha na conexão MQTT, código: {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning(f"⚠️  Desconectado inesperadamente (rc={rc}). Reconectando...")

def on_publish(client, userdata, mid):
    log.debug(f"Mensagem publicada (mid={mid})")


def criar_cliente():
    client = mqtt.Client(client_id=args.client_id, clean_session=True)
    client.username_pw_set(args.user, args.password)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish    = on_publish
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client


def conectar(client, max_tentativas=10):
    for i in range(1, max_tentativas + 1):
        try:
            log.info(f"Tentativa de conexão {i}/{max_tentativas} → {args.broker}:{args.port}")
            client.connect(args.broker, args.port, keepalive=60)
            return True
        except Exception as e:
            log.warning(f"Falha: {e}. Aguardando {i * 2}s...")
            time.sleep(i * 2)
    return False


def publicar_leitura(client, dados):
    payload = json.dumps(dados, ensure_ascii=False)

    # Tópicos individuais por grandeza
    for campo in ["temperatura", "umidade", "luminosidade"]:
        topico = f"{TOPIC_BASE}/{campo}"
        client.publish(topico, str(dados[campo]), qos=1, retain=False)
        log.debug(f"  → {topico}: {dados[campo]}")

    # Tópico com payload completo
    client.publish(f"{TOPIC_BASE}/dados", payload, qos=1, retain=False)
    log.info(
        f"📡 Publicado | T={dados['temperatura']}°C | "
        f"U={dados['umidade']}% | L={dados['luminosidade']} lux"
    )


# ─── Loop principal ──────────────────────────────────────────────────────────
def main():
    modo = "SIMULAÇÃO" if args.simulate else "HARDWARE"
    log.info(f"=== Sensor IIoT — Intel Galileo Gen 2 | Modo: {modo} ===")
    log.info(f"Broker: {args.broker}:{args.port} | Intervalo: {args.interval}s")

    client = criar_cliente()
    if not conectar(client):
        log.error("Não foi possível conectar ao broker. Encerrando.")
        sys.exit(1)

    client.loop_start()

    try:
        while True:
            dados = ler_sensores()
            publicar_leitura(client, dados)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info("Encerramento solicitado pelo usuário.")
    finally:
        client.loop_stop()
        client.disconnect()
        log.info("Sensor desconectado.")


if __name__ == "__main__":
    main()
