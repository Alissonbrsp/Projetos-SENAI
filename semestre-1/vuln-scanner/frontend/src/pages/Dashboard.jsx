/**
 * pages/Dashboard.jsx
 * Painel com métricas consolidadas e gráficos de vulnerabilidades.
 */
import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { dashboardAPI } from '../services/api'

const SEV_COLORS = {
  CRITICAL: '#e74c3c',
  HIGH:     '#e67e22',
  MEDIUM:   '#f1c40f',
  LOW:      '#27ae60',
}

function StatCard({ value, label, className }) {
  return (
    <div className={`stat-card ${className}`}>
      <div className="stat-num">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function Dashboard() {
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    dashboardAPI.getStats()
      .then((r) => setStats(r.data))
      .catch(() => setError('Erro ao carregar estatísticas. Verifique se há scans concluídos.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="main" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <span className="spinner spinner-lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="main">
        <div className="card">
          <div className="alert alert-error">{error}</div>
        </div>
      </div>
    )
  }

  const pieData = stats?.severity_trend?.filter((d) => d.count > 0).map((d) => ({
    name:  d.severity,
    value: d.count,
  })) ?? []

  const fmt = (iso) => iso ? new Date(iso).toLocaleString('pt-BR') : '-'

  return (
    <div className="main">
      <div className="card">
        <h2 className="card-title">Dashboard</h2>

        {/* Stat cards */}
        <div className="stat-grid">
          <StatCard value={stats?.total_assets}          label="Ativos Descobertos"      className="s-total"  />
          <StatCard value={stats?.total_scans}           label="Scans Realizados"        className="s-scans"  />
          <StatCard value={stats?.critical_count}        label="Critical"                className="s-crit"   />
          <StatCard value={stats?.high_count}            label="High"                    className="s-high"   />
          <StatCard value={stats?.medium_count}          label="Medium"                  className="s-medium" />
          <StatCard value={stats?.low_count}             label="Low"                     className="s-low"    />
        </div>

        {/* Gráficos */}
        <div className="charts-grid">

          {/* Barras — top serviços */}
          <div className="chart-box">
            <h3>Top Serviços Detectados</h3>
            {stats?.top_services?.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={stats.top_services}
                  layout="vertical"
                  margin={{ left: 10, right: 10 }}
                >
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="service" tick={{ fontSize: 11 }} width={72} />
                  <Tooltip
                    formatter={(v) => [v, 'Ocorrências']}
                    contentStyle={{ fontSize: 12 }}
                  />
                  <Bar dataKey="count" fill="var(--active)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <p>Nenhum serviço detectado ainda.</p>
              </div>
            )}
          </div>

          {/* Pizza — distribuição por severidade */}
          <div className="chart-box">
            <h3>Distribuição por Severidade</h3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={SEV_COLORS[entry.name] || '#888'} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v, n) => [v, n]} contentStyle={{ fontSize: 12 }} />
                  <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🛡️</div>
                <p>Nenhuma vulnerabilidade registrada ainda.</p>
              </div>
            )}
          </div>
        </div>

        {/* Totais */}
        <div style={{
          marginTop: 20,
          paddingTop: 16,
          borderTop: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.82rem',
          color: 'var(--muted)',
        }}>
          <span>Total de vulnerabilidades: <strong>{stats?.total_vulnerabilities ?? 0}</strong></span>
          <span>Último scan: <strong>{fmt(stats?.last_scan_at)}</strong></span>
        </div>
      </div>
    </div>
  )
}
