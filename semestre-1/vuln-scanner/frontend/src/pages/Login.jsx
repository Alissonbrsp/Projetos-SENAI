/**
 * pages/Login.jsx
 */
import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Login({ onGoRegister }) {
  const { login } = useAuth()

  const [form, setForm]       = useState({ username: '', password: '' })
  const [showPw, setShowPw]   = useState(false)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async () => {
    if (!form.username || !form.password) {
      setError('Preencha usuário e senha.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
    } catch (e) {
      setError(e.response?.data?.detail || 'Credenciais inválidas.')
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e) => e.key === 'Enter' && handleSubmit()

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <h1 className="auth-title">Entrar</h1>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="auth-field">
          <input
            className="input"
            placeholder="Usuário"
            value={form.username}
            onChange={set('username')}
            onKeyDown={onKey}
            autoFocus
          />
        </div>

        <div className="auth-field">
          <input
            className="input"
            placeholder="Senha"
            type={showPw ? 'text' : 'password'}
            value={form.password}
            onChange={set('password')}
            onKeyDown={onKey}
            style={{ paddingRight: 40 }}
          />
          <button className="eye-btn" onClick={() => setShowPw((v) => !v)} type="button">
            {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        <button
          className="btn btn-navy btn-full"
          style={{ marginTop: 8 }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? <span className="spinner" /> : 'Entrar'}
        </button>

        <p className="auth-link">
          Não tem conta?{' '}
          <a onClick={onGoRegister}>Clique Aqui !</a>
        </p>
      </div>
    </div>
  )
}
