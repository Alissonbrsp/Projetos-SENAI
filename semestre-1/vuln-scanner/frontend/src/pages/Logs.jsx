/**
 * pages/Logs.jsx
 * Lista de logs de auditoria com filtros por IP/serviço/porta e severidade.
 */
import { useState, useEffect } from 'react'
import { logsAPI } from '../services/api'

const SEV_OPTIONS = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']

const fmt = (iso) => iso ? new Date(iso).toLocaleString('pt-BR') : '-'

export default function Logs() {
  const [logs,    setLogs]    = useState([])
  const [search,  setSearch]  = useState('')
  const [sev,     setSev]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (search) params.search   = search
      if (sev)    params.severity = sev
      const res = await logsAPI.getLogs(params)
      setLogs(res.data)
    } catch {
      setError('Erro ao carregar logs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchLogs() }, [])

  return (
    <div className="main">
      <div className="card">
        <h2 className="card-title">LOGS</h2>

        {/* Filtros */}
        <div className="filter-bar">
          <span className="filter-label">Filtros :</span>
          <input
            className="input"
            style={{ maxWidth: 300 }}
            placeholder="Buscar por IP, serviço/porta:"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchLogs()}
          />
          <select
            className="input"
            style={{ maxWidth: 150 }}
            value={sev}
            onChange={(e) => setSev(e.target.value)}
          >
            {SEV_OPTIONS.map((s) => (
              <option key={s} value={s}>{s || 'Severidade'}</option>
            ))}
          </select>
          <button className="btn btn-navy" onClick={fetchLogs} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Aplicar'}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <span className="spinner spinner-lg" />
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Data/Hora</th>
                <th>Device / IP</th>
                <th>Porta</th>
                <th>Serviço</th>
                <th>Severidade</th>
                <th>Evento</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '28px', color: 'var(--muted)' }}>
                    Nenhum log encontrado.
                  </td>
                </tr>
              ) : (
                logs.map((lg) => (
                  <tr key={lg.id}>
                    <td style={{ whiteSpace: 'nowrap' }}>{fmt(lg.created_at)}</td>
                    <td>{lg.ip || '-'}</td>
                    <td>{lg.port || '-'}</td>
                    <td>{lg.service || '-'}</td>
                    <td><span className={`badge badge-${lg.severity}`}>{lg.severity}</span></td>
                    <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {lg.event}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
