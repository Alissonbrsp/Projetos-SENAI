/**
 * components/Sidebar.jsx
 * Barra lateral de navegação — fiel ao mockup original.
 */
import { UserCircle2, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const NAV_ITEMS = [
  { key: 'scanner',   label: 'Scanner'    },
  { key: 'dashboard', label: 'Dashboard'  },
  { key: 'reports',   label: 'Relatorios' },
  { key: 'logs',      label: 'Logs'       },
]

export default function Sidebar({ active, onNavigate }) {
  const { user, logout } = useAuth()

  return (
    <aside className="sidebar">
      {/* Perfil / Logout */}
      <div className="sidebar-profile" onClick={logout} title="Clique para sair">
        <div className="profile-icon">
          <UserCircle2 size={24} strokeWidth={1.5} />
        </div>
        <div>
          <div className="profile-name">{user?.username || 'Usuário'}</div>
          <div className="profile-hint">Clique para sair</div>
        </div>
      </div>

      {/* Navegação */}
      <nav>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            className={`nav-item ${active === item.key ? 'active' : ''}`}
            onClick={() => onNavigate(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
