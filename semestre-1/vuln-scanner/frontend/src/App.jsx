/**
 * App.jsx
 * Roteamento principal entre telas de auth e páginas autenticadas.
 */
import { useState } from 'react'
import { useAuth }   from './contexts/AuthContext'
import Sidebar       from './components/Sidebar'
import Login         from './pages/Login'
import Register      from './pages/Register'
import Scanner       from './pages/Scanner'
import Dashboard     from './pages/Dashboard'
import Reports       from './pages/Reports'
import Logs          from './pages/Logs'

const PAGES = {
  scanner:   Scanner,
  dashboard: Dashboard,
  reports:   Reports,
  logs:      Logs,
}

export default function App() {
  const { user }          = useAuth()
  const [page,     setPage]    = useState('scanner')
  const [authMode, setAuthMode] = useState('login')

  // Não autenticado
  if (!user) {
    return authMode === 'login'
      ? <Login    onGoRegister={() => setAuthMode('register')} />
      : <Register onGoLogin={()   => setAuthMode('login')}    />
  }

  const Page = PAGES[page] || Scanner

  return (
    <div className="shell">
      <Sidebar active={page} onNavigate={setPage} />
      <Page />
    </div>
  )
}
