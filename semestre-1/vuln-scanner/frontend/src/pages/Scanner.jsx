/**
 * pages/Scanner.jsx
 * Configuração e execução de varredura de rede com Nmap.
 * Faz polling do status a cada 3s até COMPLETED ou FAILED.
 */
import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Shield, ShieldAlert } from 'lucide-react'
import { scannerAPI } from '../services/api'

// ── Utilitários ───────────────────────────────────────────────────────────────

function SevBadge({ severity }) {
  return <span className={`badge badge-${severity}`}>{severity}</span>
}

// ── CVE Item ──────────────────────────────────────────────────────────────────

function CveItem({ vuln }) {
  const nist = vuln.nist_refs ? JSON.parse(vuln.nist_refs) : []
  const cis  = vuln.cis_refs  ? JSON.parse(vuln.cis_refs)  : []

  return (
    <div className="cve-item">
      <div className="cve-header">
        <span className="cve-id">{vuln.cve_id}</span>
        <SevBadge severity={vuln.severity} />
        {vuln.cvss_score && (
          <span className="cve-score">CVSS: {vuln.cvss_score}</span>
        )}
        {vuln.port && (
          <span className="cve-port">Porta {vuln.port} / {vuln.service || '-'}</span>
        )}
      </div>
      <p className="cve-desc">{vuln.description}</p>
      {nist.length > 0 && (
        <p className="cve-ref"><strong>NIST SP 800-53:</strong> {nist.join(', ')}</p>
      )}
      {cis.length > 0 && (
        <p className="cve-ref"><strong>CIS Controls v8:</strong> {cis.join(', ')}</p>
      )}
    </div>
  )
}

// ── Asset Card ────────────────────────────────────────────────────────────────

function AssetCard({ asset }) {
  const [open, setOpen] = useState(false)
  const vulnCount = asset.vulnerabilities?.length ?? 0

  return (
    <div className="asset-card">
      <div className="asset-card-header" onClick={() => setOpen((v) => !v)}>
        <span><strong>IP:</strong> {asset.ip}</span>
        {asset.mac     && <span><strong>MAC:</strong> {asset.mac}</span>}
        <span><strong>Tipo:</strong> {asset.device_type || 'Host'}</span>
        {asset.os_name && <span><strong>SO:</strong> {asset.os_name}</span>}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {vulnCount > 0 && (
            <span style={{ color: '#fca5a5', display: 'flex', alignItems: 'center', gap: 4 }}>
              <ShieldAlert size={14} />
              {vulnCount} CVE{vulnCount > 1 ? 's' : ''}
            </span>
          )}
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </div>

      {open && (
        <div className="asset-card-body">
          {/* Portas */}
          {asset.ports?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 8 }}>Portas / Serviços</p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Porta</th>
                    <th>Protocolo</th>
                    <th>Serviço</th>
                    <th>Produto</th>
                    <th>Versão</th>
                  </tr>
                </thead>
                <tbody>
                  {asset.ports.map((p) => (
                    <tr key={p.id}>
                      <td>{p.port}</td>
                      <td>{p.protocol}</td>
                      <td>{p.service || '-'}</td>
                      <td>{p.product || '-'}</td>
                      <td>{p.version || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* CVEs */}
          {vulnCount > 0 && (
            <div>
              <p style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 8 }}>
                Vulnerabilidades Correlacionadas (NVD/CVE)
              </p>
              {asset.vulnerabilities.map((v) => (
                <CveItem key={v.id} vuln={v} />
              ))}
            </div>
          )}

          {asset.ports?.length === 0 && vulnCount === 0 && (
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
              Nenhuma porta aberta ou vulnerabilidade detectada.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ── Scanner Page ──────────────────────────────────────────────────────────────

export default function Scanner() {
  const [target,  setTarget]  = useState('')
  const [options, setOptions] = useState({
    discover_assets: true,
    detect_ports:    true,
    identify_os:     false,
  })
  const [scan,    setScan]    = useState(null)
  const [assets,  setAssets]  = useState([])
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const pollRef = useRef(null)

  const stopPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const pollScan = async (id) => {
    try {
      const res = await scannerAPI.getScan(id)
      setScan(res.data.scan)
      setAssets(res.data.assets || [])
      if (['COMPLETED', 'FAILED'].includes(res.data.scan.status)) {
        stopPoll()
        setLoading(false)
      }
    } catch {
      stopPoll()
      setLoading(false)
    }
  }

  const handleStart = async () => {
    if (!target.trim()) {
      setError('Informe um alvo (ex: 192.168.1.0/24 ou 192.168.1.1).')
      return
    }
    setError('')
    setAssets([])
    setScan(null)
    stopPoll()
    setLoading(true)

    try {
      const res = await scannerAPI.startScan({ target: target.trim(), ...options })
      setScan(res.data)
      pollRef.current = setInterval(() => pollScan(res.data.id), 3000)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao iniciar o scan.')
      setLoading(false)
    }
  }

  const toggle = (key) => setOptions((o) => ({ ...o, [key]: !o[key] }))

  useEffect(() => () => stopPoll(), [])

  // Status bar
  const renderStatus = () => {
    if (!scan) return null
    if (scan.status === 'RUNNING') {
      return <div className="alert alert-info"><span className="scanning">⟳ Varrendo {scan.target}… aguarde</span></div>
    }
    if (scan.status === 'COMPLETED') {
      return (
        <div className="alert alert-success">
          ✓ Scan concluído — {assets.length} ativo(s) encontrado(s),{' '}
          {assets.reduce((n, a) => n + (a.vulnerabilities?.length ?? 0), 0)} CVE(s) correlacionado(s)
        </div>
      )
    }
    if (scan.status === 'FAILED') {
      return <div className="alert alert-error">✗ Falha: {scan.error_msg}</div>
    }
    return <div className="alert alert-info">Aguardando início…</div>
  }

  return (
    <div className="main">
      <div className="card">
        <h2 className="card-title">configuração do Scanner</h2>

        {error && <div className="alert alert-error">{error}</div>}

        <label style={{ fontWeight: 700, fontSize: '0.9rem', display: 'block', marginBottom: 6 }}>
          Sub-rede/IP:
        </label>
        <input
          className="input"
          style={{ marginBottom: 12 }}
          placeholder="Digite o IP (ex: 192.168.0.0/24)"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleStart()}
        />

        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 24 }}>
          <button className="btn btn-blue" onClick={handleStart} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Iniciar'}
          </button>

          <div className="check-group">
            {[
              ['discover_assets', 'Descobrir ativos'],
              ['detect_ports',    'Detectar Portas/Serviços'],
              ['identify_os',     'Identificar SO'],
            ].map(([key, label]) => (
              <label key={key} className="check-item">
                <input type="checkbox" checked={options[key]} onChange={() => toggle(key)} />
                {label}
              </label>
            ))}
          </div>
        </div>

        {renderStatus()}

        {assets.length > 0 && (
          <>
            <h3 style={{ fontWeight: 700, marginBottom: 14, fontSize: '1rem' }}>
              Ativos Detectados:
            </h3>
            {assets.map((a) => <AssetCard key={a.id} asset={a} />)}
          </>
        )}
      </div>
    </div>
  )
}
