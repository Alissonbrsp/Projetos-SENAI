"""
CTF IIoT Dinâmico — Backend de Gerenciamento
VM1: FastAPI + PostgreSQL + Redis

Endpoints:
  POST /api/auth/register   → Registro de jogador
  POST /api/auth/login      → Login (retorna JWT)
  POST /api/auth/logout     → Logout (libera slot de sessão)
  GET  /api/session/status  → Status da VM3 (via Lambda)
  POST /api/session/start   → Iniciar VM3 (via Lambda)
  GET  /api/health          → Health check
  POST /api/admin/reset     → Reset da VM3 (apenas admin)
"""

from __future__ import annotations

import os
import json
import httpx
import redis
import asyncpg
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

# ---------------------------------------------------------------------------
# Configuração via variáveis de ambiente
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("TOKEN_EXPIRE_MINUTES", "120"))

DB_DSN = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
LAMBDA_API_URL = os.environ["LAMBDA_API_URL"]
LAMBDA_API_KEY = os.environ.get("LAMBDA_API_KEY", "")
MAX_PLAYERS = int(os.environ.get("MAX_CONCURRENT_PLAYERS", "5"))
ADMIN_TOKEN = os.environ["ADMIN_SECRET_TOKEN"]

FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")

# ---------------------------------------------------------------------------
# Setup da aplicação
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CTF IIoT Dinâmico — API",
    description="Backend de gerenciamento da plataforma CTF IIoT",
    version="1.0.0",
    docs_url=None,   # Desabilita /docs em produção
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------------------------------------------------------------------
# Conexões (inicializadas no startup)
# ---------------------------------------------------------------------------
db_pool: asyncpg.Pool | None = None
redis_client: redis.Redis | None = None

SESSION_COUNTER_KEY = "ctf:active_sessions"
SESSION_PREFIX = "ctf:session:"


@app.on_event("startup")
async def startup():
    global db_pool, redis_client
    db_pool = await asyncpg.create_pool(DB_DSN, min_size=2, max_size=10)
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class SessionStatus(BaseModel):
    state: str
    public_ip: str | None
    ready: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "username": payload.get("username")}
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# Endpoints de Autenticação
# ---------------------------------------------------------------------------
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM players WHERE username=$1 OR email=$2",
            req.username, req.email,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Usuário ou e-mail já cadastrado.",
            )
        await conn.execute(
            "INSERT INTO players (username, email, password_hash) VALUES ($1, $2, $3)",
            req.username, req.email, hash_password(req.password),
        )
    return {"message": "Conta criada com sucesso. Faça login para continuar."}


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, password_hash FROM players WHERE username=$1",
            form.username,
        )
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
        )

    # Controle de sessões concorrentes via Redis (atômico)
    active = int(redis_client.get(SESSION_COUNTER_KEY) or 0)
    if active >= MAX_PLAYERS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Limite de {MAX_PLAYERS} jogadores simultâneos atingido. Tente mais tarde.",
        )

    redis_client.incr(SESSION_COUNTER_KEY)
    redis_client.setex(f"{SESSION_PREFIX}{user['id']}", ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")

    # Registrar último login
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET last_login=NOW(), login_count=login_count+1 WHERE id=$1",
            user["id"],
        )

    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return TokenResponse(access_token=token, username=user["username"])


@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    session_key = f"{SESSION_PREFIX}{user_id}"

    if redis_client.exists(session_key):
        redis_client.delete(session_key)
        redis_client.decr(SESSION_COUNTER_KEY)

    return {"message": "Logout realizado com sucesso."}


# ---------------------------------------------------------------------------
# Endpoints de Sessão (VM3 Lifecycle)
# ---------------------------------------------------------------------------
@app.get("/api/session/status")
async def get_session_status(current_user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{LAMBDA_API_URL}/status",
                headers={"x-api-key": LAMBDA_API_KEY},
            )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Não foi possível obter o status: {e}")


@app.post("/api/session/start")
async def start_session(current_user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LAMBDA_API_URL}/start",
                headers={"x-api-key": LAMBDA_API_KEY},
            )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Não foi possível iniciar o ambiente: {e}")


# ---------------------------------------------------------------------------
# Endpoints de Admin
# ---------------------------------------------------------------------------
@app.post("/api/admin/reset")
async def admin_reset(token: str, current_user: dict = Depends(get_current_user)):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    import asyncio, asyncssh  # type: ignore
    # Reset rápido: recria containers na VM3 via SSH
    vm3_ip = os.environ.get("VM3_IP", "")
    ssh_key = os.environ.get("VM3_SSH_KEY_PATH", "/opt/ctf-backend/keys/vm3.pem")

    try:
        async with asyncssh.connect(
            vm3_ip, username="admin",
            client_keys=[ssh_key], known_hosts=None
        ) as conn:
            result = await conn.run(
                "cd /opt/ctf && sudo docker-compose down && sudo docker-compose up -d",
                check=True,
            )
        return {"message": "Reset iniciado. Ambiente disponível em ~30 segundos.", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no reset: {e}")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    db_ok = False
    redis_ok = False

    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception:
        pass

    try:
        redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "active_sessions": int(redis_client.get(SESSION_COUNTER_KEY) or 0),
        "max_sessions": MAX_PLAYERS,
    }
