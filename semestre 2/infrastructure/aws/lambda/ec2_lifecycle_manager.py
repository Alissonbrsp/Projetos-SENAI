"""
Lambda Function: EC2 Lifecycle Manager
CTF IIoT Dinâmico — Gerencia o ciclo de vida da VM3 (CTF Arena)

Aciona via API Gateway:
  POST /session/start  → Liga a VM3
  POST /session/stop   → Desliga a VM3
  GET  /session/status → Retorna status da VM3
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

# Configuração via variáveis de ambiente (definidas na Lambda)
VM3_INSTANCE_ID = os.environ["VM3_INSTANCE_ID"]
REGION = os.environ.get("AWS_REGION", "us-east-1")

ec2 = boto3.client("ec2", region_name=REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": os.environ.get("FRONTEND_URL", "*"),
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}


def get_instance_status() -> dict:
    """Retorna o status atual da instância VM3."""
    try:
        response = ec2.describe_instance_status(
            InstanceIds=[VM3_INSTANCE_ID],
            IncludeAllInstances=True,
        )
        reservations = ec2.describe_instances(InstanceIds=[VM3_INSTANCE_ID])
        instance = reservations["Reservations"][0]["Instances"][0]

        state = instance["State"]["Name"]
        public_ip = instance.get("PublicIpAddress", None)

        return {
            "instance_id": VM3_INSTANCE_ID,
            "state": state,
            "public_ip": public_ip,
            "ready": state == "running",
        }
    except ClientError as e:
        return {"error": str(e), "state": "unknown", "ready": False}


def start_instance() -> dict:
    """Liga a instância VM3."""
    status = get_instance_status()

    if status.get("state") == "running":
        return {"message": "CTF arena já está online.", "status": status}

    if status.get("state") == "pending":
        return {"message": "CTF arena está inicializando...", "status": status}

    ec2.start_instances(InstanceIds=[VM3_INSTANCE_ID])
    return {
        "message": "CTF arena iniciando. Aguarde ~2 minutos.",
        "status": get_instance_status(),
    }


def stop_instance() -> dict:
    """Desliga a instância VM3 (apenas para admins)."""
    status = get_instance_status()

    if status.get("state") == "stopped":
        return {"message": "CTF arena já está offline.", "status": status}

    ec2.stop_instances(InstanceIds=[VM3_INSTANCE_ID])
    return {
        "message": "CTF arena sendo desligada.",
        "status": get_instance_status(),
    }


def lambda_handler(event, context):
    """Entry point da Lambda Function."""
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/")

    # Preflight CORS
    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        # Roteamento
        if path.endswith("/status") and http_method == "GET":
            body = get_instance_status()
            status_code = 200

        elif path.endswith("/start") and http_method == "POST":
            # Validação do token JWT (delegada ao API Gateway authorizer)
            body = start_instance()
            status_code = 200

        elif path.endswith("/stop") and http_method == "POST":
            # Apenas admins (validado via API Gateway)
            body = stop_instance()
            status_code = 200

        else:
            body = {"error": "Rota não encontrada."}
            status_code = 404

    except Exception as e:
        body = {"error": f"Erro interno: {str(e)}"}
        status_code = 500

    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }
