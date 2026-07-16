"""
routers/reports.py
Listagem e download de relatórios em PDF.
"""
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Scan, Asset, ScanStatusEnum
from app.core.dependencies import get_current_user
from app.services.report_service import generate_scan_report

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_filter: date | None = None,
):
    """Lista scans concluídos disponíveis para relatório, com filtro opcional por data."""
    scans = (await db.execute(
        select(Scan)
        .where(Scan.user_id == current_user.id, Scan.status == ScanStatusEnum.COMPLETED)
        .order_by(Scan.finished_at.desc())
        .limit(50)
    )).scalars().all()

    return [
        {
            "scan_id":     s.id,
            "target":      s.target,
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
        }
        for s in scans
        if not date_filter or (s.finished_at and s.finished_at.date() == date_filter)
    ]


@router.get("/{scan_id}/pdf")
async def download_pdf(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gera e retorna o relatório PDF do scan especificado."""
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
    if scan.status != ScanStatusEnum.COMPLETED:
        raise HTTPException(400, "Scan ainda não concluído.")

    pdf   = generate_scan_report(scan, scan.assets)
    fname = f"relatorio_scan_{scan_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
