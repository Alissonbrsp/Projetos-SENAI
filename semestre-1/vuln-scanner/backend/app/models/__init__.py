"""
models/__init__.py
Modelos ORM — cada classe mapeia para uma tabela no banco de dados.
"""
import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────

class SeverityEnum(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    INFO     = "INFO"


class ScanStatusEnum(str, enum.Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"


# ── User ───────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True)
    username:         Mapped[str]      = mapped_column(String(64),  unique=True, index=True, nullable=False)
    email:            Mapped[str]      = mapped_column(String(128), unique=True, index=True, nullable=False)
    hashed_password:  Mapped[str]      = mapped_column(String(256), nullable=False)
    is_active:        Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:       Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="user")


# ── Scan ───────────────────────────────────────────────────────────────────────

class Scan(Base):
    __tablename__ = "scans"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True)
    user_id:         Mapped[int]            = mapped_column(ForeignKey("users.id"), nullable=False)
    target:          Mapped[str]            = mapped_column(String(256), nullable=False)
    status:          Mapped[ScanStatusEnum] = mapped_column(SAEnum(ScanStatusEnum), default=ScanStatusEnum.PENDING)
    discover_assets: Mapped[bool]           = mapped_column(Boolean, default=True)
    detect_ports:    Mapped[bool]           = mapped_column(Boolean, default=True)
    identify_os:     Mapped[bool]           = mapped_column(Boolean, default=False)
    started_at:      Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at:     Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_msg:       Mapped[str | None]      = mapped_column(Text, nullable=True)
    created_at:      Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow)

    user:   Mapped["User"]         = relationship("User", back_populates="scans")
    assets: Mapped[list["Asset"]]  = relationship("Asset", back_populates="scan", cascade="all, delete")


# ── Asset ──────────────────────────────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    scan_id:       Mapped[int]           = mapped_column(ForeignKey("scans.id"), nullable=False)
    ip:            Mapped[str]           = mapped_column(String(45),  nullable=False)
    mac:           Mapped[str | None]    = mapped_column(String(17),  nullable=True)
    hostname:      Mapped[str | None]    = mapped_column(String(256), nullable=True)
    os_name:       Mapped[str | None]    = mapped_column(String(128), nullable=True)
    device_type:   Mapped[str | None]    = mapped_column(String(64),  nullable=True)
    discovered_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)

    scan:            Mapped["Scan"]               = relationship("Scan", back_populates="assets")
    ports:           Mapped[list["Port"]]          = relationship("Port", back_populates="asset", cascade="all, delete")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship("Vulnerability", back_populates="asset", cascade="all, delete")
    logs:            Mapped[list["Log"]]           = relationship("Log", back_populates="asset")


# ── Port ───────────────────────────────────────────────────────────────────────

class Port(Base):
    __tablename__ = "ports"

    id:         Mapped[int]          = mapped_column(Integer, primary_key=True)
    asset_id:   Mapped[int]          = mapped_column(ForeignKey("assets.id"), nullable=False)
    port:       Mapped[int]          = mapped_column(Integer, nullable=False)
    protocol:   Mapped[str]          = mapped_column(String(8),   default="tcp")
    state:      Mapped[str]          = mapped_column(String(16),  default="open")
    service:    Mapped[str | None]   = mapped_column(String(64),  nullable=True)
    product:    Mapped[str | None]   = mapped_column(String(128), nullable=True)
    version:    Mapped[str | None]   = mapped_column(String(64),  nullable=True)
    extra_info: Mapped[str | None]   = mapped_column(String(256), nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="ports")


# ── Vulnerability ──────────────────────────────────────────────────────────────

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id:           Mapped[int]            = mapped_column(Integer, primary_key=True)
    asset_id:     Mapped[int]            = mapped_column(ForeignKey("assets.id"), nullable=False)
    cve_id:       Mapped[str]            = mapped_column(String(32),  nullable=False, index=True)
    description:  Mapped[str]            = mapped_column(Text, nullable=False)
    severity:     Mapped[SeverityEnum]   = mapped_column(SAEnum(SeverityEnum), nullable=False)
    cvss_score:   Mapped[float | None]   = mapped_column(Float,       nullable=True)
    cvss_vector:  Mapped[str | None]     = mapped_column(String(256), nullable=True)
    nist_refs:    Mapped[str | None]     = mapped_column(Text, nullable=True)
    cis_refs:     Mapped[str | None]     = mapped_column(Text, nullable=True)
    port:         Mapped[int | None]     = mapped_column(Integer, nullable=True)
    service:      Mapped[str | None]     = mapped_column(String(64),  nullable=True)
    product:      Mapped[str | None]     = mapped_column(String(128), nullable=True)
    published_at: Mapped[str | None]     = mapped_column(String(32),  nullable=True)
    found_at:     Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="vulnerabilities")


# ── Log ────────────────────────────────────────────────────────────────────────

class Log(Base):
    __tablename__ = "logs"

    id:         Mapped[int]              = mapped_column(Integer, primary_key=True)
    asset_id:   Mapped[int | None]       = mapped_column(ForeignKey("assets.id"), nullable=True)
    user_id:    Mapped[int | None]       = mapped_column(ForeignKey("users.id"),  nullable=True)
    event:      Mapped[str]              = mapped_column(String(256), nullable=False)
    severity:   Mapped[SeverityEnum]     = mapped_column(SAEnum(SeverityEnum), default=SeverityEnum.INFO)
    ip:         Mapped[str | None]       = mapped_column(String(45),  nullable=True)
    port:       Mapped[int | None]       = mapped_column(Integer, nullable=True)
    service:    Mapped[str | None]       = mapped_column(String(64), nullable=True)
    detail:     Mapped[str | None]       = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]         = mapped_column(DateTime, default=datetime.utcnow, index=True)

    asset: Mapped["Asset | None"] = relationship("Asset", back_populates="logs")
