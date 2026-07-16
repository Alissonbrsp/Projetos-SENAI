"""
main.py
Ponto de entrada da aplicação VulnScanner.

Iniciar em desenvolvimento:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Documentação interativa:
    http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, scanner, dashboard, logs, reports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="VulnScanner API",
    description="Scanner passivo de vulnerabilidades — Nmap + NVD/CVE + NIST SP 800-53 + CIS Controls v8.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scanner.router)
app.include_router(dashboard.router)
app.include_router(logs.router)
app.include_router(reports.router)


@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
