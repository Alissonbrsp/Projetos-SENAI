"""
services/cve_service.py
Correlação de serviços/produtos detectados com CVEs via NVD API v2.

Referências normativas geradas automaticamente:
  • NIST SP 800-53 Rev. 5
  • CIS Controls v8
"""
import asyncio
import json
from typing import Any
import httpx

from app.config import get_settings
from app.models import SeverityEnum

settings = get_settings()

# ── Mapeamento CVSS → Severidade (padrão NIST) ────────────────────────────────

def _cvss_to_severity(score: float | None) -> SeverityEnum:
    if score is None:  return SeverityEnum.INFO
    if score >= 9.0:   return SeverityEnum.CRITICAL
    if score >= 7.0:   return SeverityEnum.HIGH
    if score >= 4.0:   return SeverityEnum.MEDIUM
    if score > 0.0:    return SeverityEnum.LOW
    return SeverityEnum.INFO


# ── Referências NIST SP 800-53 por serviço ────────────────────────────────────

_NIST: dict[str, list[str]] = {
    "http":     ["SC-8",  "SC-23", "SI-2",  "RA-5"],
    "https":    ["SC-8",  "SC-23", "IA-2",  "SI-2"],
    "ssh":      ["AC-17", "IA-2",  "SC-8",  "CM-7"],
    "ftp":      ["SC-8",  "AC-17", "SI-2",  "CM-7"],
    "telnet":   ["AC-17", "SC-8",  "CM-7",  "SI-2"],
    "smb":      ["AC-3",  "CM-7",  "SI-2",  "SC-8"],
    "mysql":    ["AC-3",  "AU-9",  "SI-2",  "SC-28"],
    "postgres": ["AC-3",  "AU-9",  "SI-2",  "SC-28"],
    "snmp":     ["AC-17", "CM-7",  "SC-8",  "IA-3"],
    "rdp":      ["AC-17", "IA-2",  "SC-8",  "SI-2"],
    "modbus":   ["CM-7",  "SC-8",  "SI-2",  "AC-17"],
    "rtsp":     ["AC-17", "CM-7",  "SC-8"],
    "mqtt":     ["IA-3",  "SC-8",  "CM-7"],
}

# ── Referências CIS Controls v8 por serviço ───────────────────────────────────

_CIS: dict[str, list[str]] = {
    "http":     ["CIS-2",  "CIS-7",  "CIS-16"],
    "https":    ["CIS-2",  "CIS-7",  "CIS-16"],
    "ssh":      ["CIS-4",  "CIS-12", "CIS-16"],
    "ftp":      ["CIS-4",  "CIS-12", "CIS-16"],
    "telnet":   ["CIS-4",  "CIS-12", "CIS-16"],
    "smb":      ["CIS-4",  "CIS-6",  "CIS-16"],
    "mysql":    ["CIS-3",  "CIS-6",  "CIS-16"],
    "postgres": ["CIS-3",  "CIS-6",  "CIS-16"],
    "snmp":     ["CIS-4",  "CIS-12"],
    "rdp":      ["CIS-4",  "CIS-12", "CIS-16"],
    "modbus":   ["CIS-4",  "CIS-12", "CIS-18"],
    "rtsp":     ["CIS-4",  "CIS-12"],
    "mqtt":     ["CIS-4",  "CIS-12", "CIS-13"],
}

_DEFAULT_NIST = ["SI-2", "CM-7", "RA-5"]
_DEFAULT_CIS  = ["CIS-2", "CIS-7"]


def _get_refs(service: str | None) -> tuple[str, str]:
    key  = (service or "").lower()
    nist = _NIST.get(key, _DEFAULT_NIST)
    cis  = _CIS.get(key,  _DEFAULT_CIS)
    return json.dumps(nist), json.dumps(cis)


# ── Consulta NVD ──────────────────────────────────────────────────────────────

async def _query_nvd(keyword: str, max_results: int = 5) -> list[dict]:
    """Consulta a API NVD v2 e retorna CVEs normalizados."""
    headers = {"User-Agent": "VulnScanner/1.0"}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key

    params = {
        "keywordSearch":    keyword,
        "resultsPerPage":   max_results,
        "keywordExactMatch": False,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(settings.nvd_base_url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []   # Falha silenciosa: o scanner não deve parar por indisponibilidade do NVD

    cves: list[dict] = []

    for item in data.get("vulnerabilities", []):
        cve    = item.get("cve", {})
        cve_id = cve.get("id", "N/A")

        # Descrição em inglês
        descs = cve.get("descriptions", [])
        desc  = next((d["value"] for d in descs if d.get("lang") == "en"),
                     descs[0]["value"] if descs else "Sem descrição.")

        # CVSS: tenta v3.1 → v3.0 → v2.0
        score, vector = None, None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metrics = cve.get("metrics", {}).get(key, [])
            if metrics:
                cvss_data = metrics[0].get("cvssData", {})
                score     = cvss_data.get("baseScore")
                vector    = cvss_data.get("vectorString")
                break

        cves.append({
            "cve_id":       cve_id,
            "description":  desc,
            "cvss_score":   score,
            "cvss_vector":  vector,
            "severity":     _cvss_to_severity(score),
            "published_at": cve.get("published", "")[:10],
        })

    return cves


# ── Correlação principal ──────────────────────────────────────────────────────

async def correlate_vulnerabilities(ports: list[dict]) -> list[dict[str, Any]]:
    """
    Recebe lista de portas do nmap e retorna vulnerabilidades correlacionadas
    com referências NIST SP 800-53 e CIS Controls v8.
    """
    seen:   set[str]   = set()
    result: list[dict] = []

    # Semáforo para respeitar rate limit do NVD
    sem = asyncio.Semaphore(2)

    async def fetch(port: dict):
        product = port.get("product") or ""
        version = port.get("version") or ""
        service = port.get("service") or ""
        keyword = f"{product} {version}".strip() if product else service
        if not keyword:
            return []

        async with sem:
            await asyncio.sleep(0.3)
            return port, await _query_nvd(keyword)

    tasks   = [fetch(p) for p in ports]
    fetched = await asyncio.gather(*tasks, return_exceptions=True)

    for item in fetched:
        if isinstance(item, Exception) or not item:
            continue
        port, cves = item
        nist_json, cis_json = _get_refs(port.get("service"))

        for cve in cves:
            if cve["cve_id"] in seen:
                continue
            seen.add(cve["cve_id"])
            result.append({
                **cve,
                "port":      port.get("port"),
                "service":   port.get("service"),
                "product":   port.get("product"),
                "nist_refs": nist_json,
                "cis_refs":  cis_json,
            })

    return result
