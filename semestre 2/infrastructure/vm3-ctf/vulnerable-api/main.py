"""
CTF IIoT Dinâmico — Vulnerable API (VM3, container de isca)
Simula uma API industrial. Serve como ponto de investigação para o jogador.
"""
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fábrica Conectada SA — API de Telemetria", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET"], allow_headers=["*"])

INFLUX_URL = os.environ.get("INFLUX_URL", "http://influxdb:8086")
INFLUX_DB  = os.environ.get("INFLUX_DB", "ctf_sensors")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "telemetry-api", "version": "1.0.0"}


@app.get("/api/sensors")
async def list_sensors():
    """Lista os sensores registrados no sistema."""
    return {
        "sensors": [
            {"id": "sensor01", "location": "Linha-A", "type": "DHT22+LDR",
             "status": "active", "last_seen": "online"},
        ]
    }


@app.get("/api/sensors/{sensor_id}/latest")
async def latest_reading(sensor_id: str):
    """Retorna a leitura mais recente de um sensor."""
    if sensor_id != "sensor01":
        raise HTTPException(status_code=404, detail="Sensor não encontrado.")

    try:
        query = f'SELECT last("value") FROM /.*/ WHERE "sensor"=\'{sensor_id}\''
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{INFLUX_URL}/query",
                params={"db": INFLUX_DB, "q": query},
                auth=("influx_admin", "1nflux_S3cur3_P4ss!"),
            )
        if resp.status_code == 200:
            return {"sensor": sensor_id, "data": resp.json()}
        return {"sensor": sensor_id, "data": None, "message": "Sem dados recentes."}
    except Exception:
        return {"sensor": sensor_id, "data": None, "message": "Banco de dados indisponível."}


@app.get("/api/status")
async def system_status():
    """Status geral do sistema industrial."""
    return {
        "system": "Fábrica Conectada SA",
        "environment": "production",
        "broker": os.environ.get("MQTT_HOST", "vm2-broker"),
        "database": "influxdb:8086",
        "active_sensors": 1,
        "alerts": [],
    }
