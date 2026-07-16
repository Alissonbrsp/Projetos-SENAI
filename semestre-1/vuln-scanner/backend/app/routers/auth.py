"""
routers/auth.py
Registro e autenticação de usuários.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, Token, LoginForm
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registra um novo usuário. Username e e-mail devem ser únicos."""
    exists = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username ou e-mail já cadastrado.")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: LoginForm, db: AsyncSession = Depends(get_db)):
    """Autentica o usuário e retorna um token JWT."""
    result = await db.execute(select(User).where(User.username == data.username))
    user: User | None = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas.")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Conta desativada.")

    return {"access_token": create_access_token({"sub": user.username}), "token_type": "bearer"}
