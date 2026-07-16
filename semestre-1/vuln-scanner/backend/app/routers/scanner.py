"""
routers/scanner.py
Endpoints para configuração e execução de varreduras de rede.
"""
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db, AsyncSessionLocal
from app.models import User, Scan, Asset, Port, Vulnerability, Log, ScanStatusEnum, SeverityEnum
from app.schemas import ScanCreate, ScanOut, AssetOut
from app.core.dependencies import get_current_user
from app.services.nmap_service import run_nmap_scan
from app.services.cve_service import correlate_vulnerabilities

router = APIRouter(prefix="/scanner", tags=["Scanner"])


def _scan_to_out(scan: Scan, asset_count: int = 0, vuln_count: int = 0) -> ScanOut:
    return ScanOut(
        id=scan.id, target=scan.target, status=scan.status,
        discover_assets=scan.discover_assets, detect_ports=scan.detect_ports,
        identify_os=scan.identify_os, started_at=scan.started_at,
        finished_at=scan.finished_at, created_at=scan.created_at,
        error_msg=scan.error_msg, asset_count=asset_count, vuln_count=vuln_count,
    )


async def _execute_scan(scan_id: int) -> None:
    """Tarefa de background: executa nmap, persiste resultados e correlaciona CVEs."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan: Scan = result.scalar_one_or_none()
        if not scan:
            return

        scan.status     = ScanStatusEnum.RUNNING
        scan.started_at = datetime.utcnow()
        await db.commit()

        try:
            hosts = await run_nmap_scan(
                target=scan.target,
                detect_ports=scan.detect_ports,
                identify_os=scan.identify_os,
            )

            for host in hosts:
                asset = Asset(
                    scan_id=scan.id,
                    ip=host["ip"],
                    mac=host.get("mac"),
                    hostname=host.get("hostname"),
                    os_name=host.get("os_name"),
                    device_type=host.get("device_type"),
                )
                db.add(asset)
                await db.flush()

                for pd in host.get("ports", []):
                    db.add(Port(
                        asset_id=asset.id,
                        port=pd["port"], protocol=pd["protocol"], state=pd["state"],
                        service=pd.get("service"), product=pd.get("product"),
                        version=pd.get("version"), extra_info=pd.get("extra_info"),
                    ))

                vulns = await correlate_vulnerabilities(host.get("ports", []))
                for vd in vulns:
                    db.add(Vulnerability(
                        asset_id=asset.id,
                        cve_id=vd["cve_id"], description=vd["description"],
                        severity=vd["severity"], cvss_score=vd.get("cvss_score"),
                        cvss_vector=vd.get("cvss_vector"), nist_refs=vd.get("nist_refs"),
                        cis_refs=vd.get("cis_refs"), port=vd.get("port"),
                        service=vd.get("service"), product=vd.get("product"),
                        published_at=vd.get("published_at"),
                    ))
                    db.add(Log(
                        asset_id=asset.id, user_id=scan.user_id,
                        event=f"CVE: {vd['cve_id']} — {vd['severity'].value}",
                        severity=vd["severity"], ip=asset.ip,
                        port=vd.get("port"), service=vd.get("service"),
                    ))

                db.add(Log(
                    asset_id=asset.id, user_id=scan.user_id,
                    event=f"Host descoberto: {asset.ip}",
                    severity=SeverityEnum.INFO, ip=asset.ip,
                ))

            scan.status      = ScanStatusEnum.COMPLETED
            scan.finished_at = datetime.utcnow()

        except Exception as exc:
            scan.status    = ScanStatusEnum.FAILED
            scan.error_msg = str(exc)
            db.add(Log(user_id=scan.user_id, event=f"Scan falhou: {exc}", severity=SeverityEnum.HIGH))

        await db.commit()


@router.post("/scan", response_model=ScanOut, status_code=202)
async def create_scan(
    data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria e inicia uma varredura em background. Retorna imediatamente com status PENDING."""
    scan = Scan(
        user_id=current_user.id,
        target=data.target,
        discover_assets=data.discover_assets,
        detect_ports=data.detect_ports,
        identify_os=data.identify_os,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    background_tasks.add_task(_execute_scan, scan.id)
    return _scan_to_out(scan)


@router.get("/scan/{scan_id}", response_model=dict)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna o status e os resultados de um scan."""
    result = await db.execute(
        select(Scan)
        .where(Scan.id == scan_id, Scan.user_id == current_user.id)
        .options(
            selectinload(Scan.assets).selectinload(Asset.ports),
            selectinload(Scan.assets).selectinload(Asset.vulnerabilities),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan não encontrado.")

    assets     = [AssetOut.model_validate(a) for a in scan.assets]
    vuln_count = sum(len(a.vulnerabilities) for a in scan.assets)
    return {"scan": _scan_to_out(scan, len(scan.assets), vuln_count), "assets": assets}


@router.get("/scans", response_model=list[ScanOut])
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """Lista o histórico de scans do usuário autenticado."""
    result = await db.execute(
        select(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .limit(limit).offset(offset)
    )
    return [_scan_to_out(s) for s in result.scalars().all()]
