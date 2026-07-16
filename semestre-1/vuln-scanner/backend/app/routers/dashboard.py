"""
routers/dashboard.py
Métricas consolidadas para o painel de controle.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Scan, Asset, Port, Vulnerability, Log, SeverityEnum, ScanStatusEnum
from app.schemas import DashboardStats
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna estatísticas gerais para o dashboard."""
    scan_ids = (await db.execute(
        select(Scan.id).where(Scan.user_id == current_user.id)
    )).scalars().all()

    asset_ids = (await db.execute(
        select(Asset.id).where(Asset.scan_id.in_(scan_ids))
    )).scalars().all() if scan_ids else []

    # Contagem por severidade
    sev_counts = {s: 0 for s in SeverityEnum}
    if asset_ids:
        rows = (await db.execute(
            select(Vulnerability.severity, func.count(Vulnerability.id))
            .where(Vulnerability.asset_id.in_(asset_ids))
            .group_by(Vulnerability.severity)
        )).all()
        for sev, cnt in rows:
            sev_counts[sev] = cnt

    # Último scan concluído
    last_scan_at = (await db.execute(
        select(Scan.finished_at)
        .where(Scan.user_id == current_user.id, Scan.status == ScanStatusEnum.COMPLETED)
        .order_by(Scan.finished_at.desc()).limit(1)
    )).scalar_one_or_none()

    # Top 5 serviços detectados
    top_services = []
    if asset_ids:
        top_services = [
            {"service": s, "count": c}
            for s, c in (await db.execute(
                select(Port.service, func.count(Port.id).label("c"))
                .where(Port.asset_id.in_(asset_ids), Port.service.isnot(None))
                .group_by(Port.service)
                .order_by(func.count(Port.id).desc())
                .limit(5)
            )).all()
        ]

    return DashboardStats(
        total_assets=len(asset_ids),
        total_vulnerabilities=sum(sev_counts.values()),
        critical_count=sev_counts[SeverityEnum.CRITICAL],
        high_count=sev_counts[SeverityEnum.HIGH],
        medium_count=sev_counts[SeverityEnum.MEDIUM],
        low_count=sev_counts[SeverityEnum.LOW],
        total_scans=len(scan_ids),
        last_scan_at=last_scan_at,
        top_services=top_services,
        severity_trend=[
            {"severity": s.value, "count": sev_counts[s]}
            for s in [SeverityEnum.CRITICAL, SeverityEnum.HIGH, SeverityEnum.MEDIUM, SeverityEnum.LOW]
        ],
    )
