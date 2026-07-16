/**
 * pages/Register.jsx
 */
import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Register({ onGoLogin }) {
  const { register, login } = useAuth()

  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' })
  const [show, setShow] = useState({ pw: false, confirm: false })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const set  = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const tog  = (key) => setShow((s) => ({ ...s, [key]: !s[key] }))

  const handleSubmit = async () => {
    if (!form.username || !form.email || !form.password) {
      setError('Preencha todos os campos.')
      return
    }
    if (form.password !== form.confirm) {
      setError('As senhas não coincidem.')
      return
    }
    if (form.password.length < 6) {
      setError('A senha deve ter no mínimo 6 caracteres.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await register({ username: form.username, email: form.email, password: form.password })
      await login(form.username, form.password)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao registrar. Tente outro usuário ou e-mail.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <h1 className="auth-title">Registre-se</h1>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="auth-field">
          <input className="input" placeholder="Usuário" value={form.username} onChange={set('username')} autoFocus />
        </div>

        <div className="auth-field">
          <input className="input" placeholder="Email" type="email" value={form.email} onChange={set('email')} />
        </div>

        <div className="auth-field">
          <input
            className="input"
            placeholder="Senha"
            type={show.pw ? 'text' : 'password'}
            value={form.password}
            onChange={set('password')}
            style={{ paddingRight: 40 }}
          />
          <button className="eye-btn" onClick={() => tog('pw')} type="button">
            {show.pw ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        <div className="auth-field">
          <input
            className="input"
            placeholder="Confirmar Senha"
            type={show.confirm ? 'text' : 'password'}
            value={form.confirm}
            onChange={set('confirm')}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            style={{ paddingRight: 40 }}
          />
          <button className="eye-btn" onClick={() => tog('confirm')} type="button">
            {show.confirm ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        <button
          className="btn btn-navy btn-full"
          style={{ marginTop: 8 }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? <span className="spinner" /> : 'Registrar'}
        </button>

        <p className="auth-link">
          Já tem uma conta? <a onClick={onGoLogin}>Clique Aqui !</a>
        </p>
      </div>
    </div>
  )
}
