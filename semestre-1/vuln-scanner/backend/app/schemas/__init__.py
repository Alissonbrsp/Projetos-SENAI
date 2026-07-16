"""
schemas/__init__.py
Contratos Pydantic v2 para entrada e saída da API.
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models import SeverityEnum, ScanStatusEnum


# ── Auth ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str  = Field(..., min_length=3, max_length=64)
    email:    EmailStr
    password: str  = Field(..., min_length=6)


class UserOut(BaseModel):
    id:         int
    username:   str
    email:      str
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class LoginForm(BaseModel):
    username: str
    password: str


# ── Port ───────────────────────────────────────────────────────────────────────

class PortOut(BaseModel):
    id:         int
    port:       int
    protocol:   str
    state:      str
    service:    str | None
    product:    str | None
    version:    str | None
    extra_info: str | None
    model_config = {"from_attributes": True}


# ── Vulnerability ──────────────────────────────────────────────────────────────

class VulnOut(BaseModel):
    id:           int
    cve_id:       str
    description:  str
    severity:     SeverityEnum
    cvss_score:   float | None
    cvss_vector:  str | None
    nist_refs:    str | None
    cis_refs:     str | None
    port:         int | None
    service:      str | None
    product:      str | None
    published_at: str | None
    model_config = {"from_attributes": True}


# ── Asset ──────────────────────────────────────────────────────────────────────

class AssetOut(BaseModel):
    id:              int
    ip:              str
    mac:             str | None
    hostname:        str | None
    os_name:         str | None
    device_type:     str | None
    discovered_at:   datetime
    ports:           list[PortOut]  = []
    vulnerabilities: list[VulnOut]  = []
    model_config = {"from_attributes": True}


# ── Scan ───────────────────────────────────────────────────────────────────────

class ScanCreate(BaseModel):
    target:          str  = Field(..., example="192.168.1.0/24")
    discover_assets: bool = True
    detect_ports:    bool = True
    identify_os:     bool = False


class ScanOut(BaseModel):
    id:              int
    target:          str
    status:          ScanStatusEnum
    discover_assets: bool
    detect_ports:    bool
    identify_os:     bool
    started_at:      datetime | None
    finished_at:     datetime | None
    created_at:      datetime
    error_msg:       str | None
    asset_count:     int = 0
    vuln_count:      int = 0
    model_config = {"from_attributes": True}


# ── Log ────────────────────────────────────────────────────────────────────────

class LogOut(BaseModel):
    id:         int
    event:      str
    severity:   SeverityEnum
    ip:         str | None
    port:       int | None
    service:    str | None
    detail:     str | None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_assets:          int
    total_vulnerabilities: int
    critical_count:        int
    high_count:            int
    medium_count:          int
    low_count:             int
    total_scans:           int
    last_scan_at:          datetime | None
    top_services:          list[dict]
    severity_trend:        list[dict]
