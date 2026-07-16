"""
services/nmap_service.py
Varredura de rede não-intrusiva usando python-nmap.

Estratégia passiva/leve:
  - Timing T3 (moderado)
  - Sem scripts agressivos
  - Detecção de versão com intensidade baixa (3/9)
  - Máximo de 2 retransmissões
"""
import asyncio
from typing import Any
import nmap

# Mapeamento porta → tipo de dispositivo (heurística)
_DEVICE_HINTS: dict[int, str] = {
    21:   "FTP Server",
    22:   "SSH Server",
    23:   "Telnet Device",
    25:   "Mail Server",
    53:   "DNS Server",
    80:   "Web Server",
    102:  "S7 PLC (ICS)",
    161:  "SNMP Device",
    443:  "Web Server (HTTPS)",
    502:  "Modbus Device (ICS)",
    554:  "IP Camera / RTSP",
    1883: "MQTT Broker (IoT)",
    3306: "Database Server",
    3389: "RDP Server",
    5432: "Database Server",
    5900: "VNC Device",
    8883: "MQTT Broker (IoT/TLS)",
    9100: "Network Printer",
}


def _build_args(detect_ports: bool, identify_os: bool) -> str:
    args = ["-T3", "--max-retries 2", "--open"]
    if not detect_ports:
        args.append("-sn")
    else:
        args.extend(["-sV", "--version-intensity 3"])
    if identify_os:
        args.append("-O")
    return " ".join(args)


def _guess_device(ports: dict) -> str:
    for port_num in ports:
        hint = _DEVICE_HINTS.get(int(port_num))
        if hint:
            return hint
        service = ports[port_num].get("name", "").lower()
        if "http" in service:
            return "Web Server"
        if "ssh" in service:
            return "SSH Server"
        if "mysql" in service or "postgres" in service:
            return "Database Server"
    return "Host"


def _run_scan(target: str, detect_ports: bool, identify_os: bool) -> list[dict[str, Any]]:
    """Executa o nmap de forma síncrona. Chamado via asyncio.to_thread()."""
    nm   = nmap.PortScanner()
    args = _build_args(detect_ports, identify_os)

    try:
        nm.scan(hosts=target, arguments=args)
    except nmap.PortScannerError as exc:
        raise RuntimeError(f"Erro nmap: {exc}") from exc

    results: list[dict] = []

    for host in nm.all_hosts():
        if nm[host].state() != "up":
            continue

        info      = nm[host]
        hostnames = info.hostnames()
        tcp_ports = info.get("tcp", {})
        udp_ports = info.get("udp", {})

        # Sistema operacional
        os_name = None
        if identify_os and info.get("osmatch"):
            os_name = info["osmatch"][0].get("name")

        # Portas abertas
        port_list: list[dict] = []
        for proto, pdict in [("tcp", tcp_ports), ("udp", udp_ports)]:
            for num, data in pdict.items():
                if data.get("state") == "open":
                    port_list.append({
                        "port":       int(num),
                        "protocol":   proto,
                        "state":      "open",
                        "service":    data.get("name"),
                        "product":    data.get("product"),
                        "version":    data.get("version"),
                        "extra_info": data.get("extrainfo"),
                    })

        results.append({
            "ip":          host,
            "mac":         info["addresses"].get("mac"),
            "hostname":    hostnames[0]["name"] if hostnames else None,
            "os_name":     os_name,
            "device_type": _guess_device(tcp_ports),
            "ports":       port_list,
        })

    return results


async def run_nmap_scan(
    target: str,
    detect_ports: bool = True,
    identify_os: bool  = False,
) -> list[dict[str, Any]]:
    """Executa o scan em thread separada para não bloquear o event loop."""
    return await asyncio.to_thread(_run_scan, target, detect_ports, identify_os)
