"""
database.py
Configuração do SQLAlchemy assíncrono com SQLite via aiosqlite.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Converte sqlite:/// → sqlite+aiosqlite:///
_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependência FastAPI: abre e fecha a sessão por request."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Cria todas as tabelas se não existirem."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
