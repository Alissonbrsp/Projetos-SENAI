"""
core/dependencies.py
Dependências reutilizáveis injetadas via FastAPI Depends().
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import decode_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Valida o JWT e retorna o usuário autenticado. Lança 401 se inválido."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload:
        raise exc

    username: str | None = payload.get("sub")
    if not username:
        raise exc

    result = await db.execute(select(User).where(User.username == username))
    user   = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise exc

    return user
