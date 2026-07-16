"""
services/report_service.py
Geração de relatórios PDF profissionais com fpdf2.
"""
import json
from datetime import datetime
from fpdf import FPDF, XPos, YPos
from app.models import Scan, Asset, SeverityEnum

_SEV_RGB = {
    SeverityEnum.CRITICAL: (192, 57,  43),
    SeverityEnum.HIGH:     (211, 84,   0),
    SeverityEnum.MEDIUM:   (183, 149,  0),
    SeverityEnum.LOW:      ( 30, 132, 73),
    SeverityEnum.INFO:     ( 52, 152,219),
}


class _PDF(FPDF):
    def header(self):
        self.set_fill_color(13, 66, 120)
        self.rect(0, 0, 210, 24, "F")
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(0, 8, "VulnScanner — Relatório de Vulnerabilidades", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 8)
        self.set_x(10)
        self.cell(0, 5, f"Gerado em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC")
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def section(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(13, 66, 120)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def kv(self, label: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.cell(55, 6, label + ":", border="B")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, value, border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate_scan_report(scan: Scan, assets: list[Asset]) -> bytes:
    """Gera e retorna o PDF do relatório como bytes."""
    pdf = _PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=18)

    all_vulns = [v for a in assets for v in (a.vulnerabilities or [])]
    sev_count = {s: 0 for s in SeverityEnum}
    for v in all_vulns:
        sev_count[v.severity] += 1

    # ── Sumário executivo
    pdf.section("1. Sumário Executivo")
    for label, value in [
        ("Alvo",               scan.target),
        ("Status",             scan.status.value),
        ("Início",             scan.started_at.strftime("%d/%m/%Y %H:%M") if scan.started_at else "-"),
        ("Término",            scan.finished_at.strftime("%d/%m/%Y %H:%M") if scan.finished_at else "-"),
        ("Total de Ativos",    str(len(assets))),
        ("Total de CVEs",      str(len(all_vulns))),
        ("  Critical",         str(sev_count[SeverityEnum.CRITICAL])),
        ("  High",             str(sev_count[SeverityEnum.HIGH])),
        ("  Medium",           str(sev_count[SeverityEnum.MEDIUM])),
        ("  Low",              str(sev_count[SeverityEnum.LOW])),
    ]:
        pdf.kv(label, value)

    pdf.ln(6)
    pdf.section("2. Ativos e Vulnerabilidades")

    for asset in assets:
        # Cabeçalho do ativo
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(26, 58, 92)
        pdf.cell(0, 7, f"  IP: {asset.ip}  |  MAC: {asset.mac or 'N/A'}  |  SO: {asset.os_name or 'N/A'}  |  Tipo: {asset.device_type or 'N/A'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        # Tabela de portas
        if asset.ports:
            pdf.set_font("Helvetica", "B", 8)
            for col, w in [("Porta",8),("Proto",10),("Serviço",25),("Produto",45),("Versão",30)]:
                pdf.cell(w*2, 5, col, border=1)
            pdf.ln()
            pdf.set_font("Helvetica", "", 8)
            for p in asset.ports:
                for val, w in [(str(p.port),8),(p.protocol,10),(p.service or "-",25),(p.product or "-",45),(p.version or "-",30)]:
                    pdf.cell(w*2, 5, val[:20], border=1)
                pdf.ln()
            pdf.ln(2)

        # CVEs
        if asset.vulnerabilities:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "  CVEs Correlacionados:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for v in asset.vulnerabilities:
                r, g, b = _SEV_RGB.get(v.severity, (80, 80, 80))
                pdf.set_text_color(r, g, b)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(0, 5, f"  [{v.severity.value}] {v.cve_id}  CVSS: {v.cvss_score or 'N/A'}  Porta: {v.port or '-'}/{v.service or '-'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(60, 60, 60)
                pdf.set_font("Helvetica", "", 7)
                desc = v.description[:240] + "..." if len(v.description) > 240 else v.description
                pdf.multi_cell(0, 4, f"  {desc}")
                if v.nist_refs:
                    pdf.set_text_color(13, 66, 120)
                    pdf.cell(0, 4, f"  NIST SP 800-53: {', '.join(json.loads(v.nist_refs))}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                if v.cis_refs:
                    pdf.cell(0, 4, f"  CIS Controls v8: {', '.join(json.loads(v.cis_refs))}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)

        pdf.ln(4)

    return bytes(pdf.output())
