"""
routers/logs.py
Consulta de logs de auditoria com filtros.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, cast, String

from app.database import get_db
from app.models import User, Log, SeverityEnum
from app.schemas import LogOut
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=list[LogOut])
async def list_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search:   str | None          = Query(None, description="Busca por IP, serviço ou porta"),
    severity: SeverityEnum | None = Query(None, description="Filtro de severidade"),
    limit:    int = Query(100, le=500),
    offset:   int = 0,
):
    """Lista logs de auditoria com filtros opcionais por texto e severidade."""
    conditions = [Log.user_id == current_user.id]

    if severity:
        conditions.append(Log.severity == severity)

    if search:
        conditions.append(or_(
            Log.ip.ilike(f"%{search}%"),
            Log.service.ilike(f"%{search}%"),
            Log.event.ilike(f"%{search}%"),
            cast(Log.port, String).ilike(f"%{search}%"),
        ))

    stmt = (
        select(Log)
        .where(and_(*conditions))
        .order_by(Log.created_at.desc())
        .limit(limit).offset(offset)
    )

    logs = (await db.execute(stmt)).scalars().all()
    return [LogOut.model_validate(lg) for lg in logs]
