/**
 * pages/Reports.jsx
 * Lista relatórios de scans concluídos e permite download em PDF.
 */
import { useState, useEffect } from 'react'
import { Download, FileText } from 'lucide-react'
import { reportsAPI } from '../services/api'

const fmt = (iso) => iso ? new Date(iso).toLocaleString('pt-BR') : '-'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [date,    setDate]    = useState('')
  const [loading, setLoading] = useState(false)
  const [dlId,    setDlId]    = useState(null)
  const [error,   setError]   = useState('')

  const fetchReports = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await reportsAPI.list(date || undefined)
      setReports(res.data)
    } catch {
      setError('Erro ao carregar relatórios.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReports() }, [])

  const handleDownload = async (id) => {
    setDlId(id)
    try {
      const res  = await reportsAPI.downloadPDF(id)
      const url  = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href  = url
      link.download = `relatorio_scan_${id}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Erro ao baixar o PDF. Tente novamente.')
    } finally {
      setDlId(null)
    }
  }

  return (
    <div className="main">
      <div className="card">
        <h2 className="card-title">Relatorios</h2>

        {/* Filtro por data */}
        <div className="filter-bar" style={{ marginBottom: 24 }}>
          <input
            className="input"
            type="date"
            style={{ maxWidth: 220 }}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <button className="btn btn-navy" onClick={fetchReports} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Aplicar'}
          </button>
          {date && (
            <button
              className="btn"
              style={{ background: 'transparent', color: 'var(--muted)', border: '1px solid var(--border)' }}
              onClick={() => { setDate(''); fetchReports() }}
            >
              Limpar
            </button>
          )}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <span className="spinner spinner-lg" />
          </div>
        ) : reports.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"><FileText size={48} /></div>
            <p style={{ fontWeight: 600 }}>Nenhum relatório disponível.</p>
            <p style={{ fontSize: '0.85rem', marginTop: 6 }}>
              Execute um scan para gerar relatórios em PDF.
            </p>
          </div>
        ) : (
          reports.map((r) => (
            <div key={r.scan_id} className="report-item">
              <div>
                <div className="report-target">Scan #{r.scan_id} — {r.target}</div>
                <div className="report-date">Concluído em {fmt(r.finished_at)}</div>
              </div>
              <button
                className="btn btn-navy"
                onClick={() => handleDownload(r.scan_id)}
                disabled={dlId === r.scan_id}
              >
                {dlId === r.scan_id
                  ? <span className="spinner" />
                  : <><Download size={15} /> PDF</>
                }
              </button>
            </div>
          ))
        )}
      </div>

      {/* FAB — download do relatório mais recente */}
      {reports.length > 0 && (
        <button
          className="fab"
          title="Baixar relatório mais recente"
          onClick={() => handleDownload(reports[0].scan_id)}
          disabled={dlId !== null}
        >
          <Download size={20} />
        </button>
      )}
    </div>
  )
}
